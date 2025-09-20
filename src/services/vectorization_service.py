"""
Vectorization service for processing database content and storing embeddings.

This service takes configured tables/columns and creates embeddings that are
stored in ChromaDB for similarity search and hybrid retrieval.
"""

import logging
from typing import List, Dict, Any, Optional, Generator, Tuple, cast
from datetime import datetime
import json
import hashlib

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
import numpy as np

from src.database.models import (
    TableConfig, ColumnConfig, VectorizationJob, 
    VectorizationStatus, VectorizationStrategy
)
from src.database.database import get_db_session_context
from src.database.chroma_db import ChromaCache
from src.llm.google import get_gemini_embeddings


logger = logging.getLogger(__name__)


class VectorizationService:
    """
    Service for vectorizing database content and storing in ChromaDB.
    """
    
    def __init__(self):
        self.embedding_model = get_gemini_embeddings()
        self.chroma_cache = ChromaCache()
        self.batch_size = 50  # Number of records to process at once
        self.max_text_length = 8000  # Maximum text length for embedding
    
    def start_vectorization_job(self, table_config_id: int, user_id: Optional[str] = None) -> VectorizationJob:
        """
        Start a new vectorization job for a table configuration.
        
        Args:
            table_config_id: ID of the table configuration
            user_id: Optional user ID who started the job
            
        Returns:
            Created VectorizationJob instance
        """
        with get_db_session_context() as session:
            table_config = session.query(TableConfig).get(table_config_id)
            if not table_config:
                raise ValueError("Table configuration not found")
            
            if not table_config.is_enabled:
                raise ValueError("Table configuration is disabled")
            
            # Check for existing running jobs
            existing_job = (
                session.query(VectorizationJob)
                .filter(VectorizationJob.table_config_id == table_config_id)
                .filter(VectorizationJob.status.in_([VectorizationStatus.PENDING, VectorizationStatus.IN_PROGRESS]))
                .first()
            )
            
            if existing_job:
                raise ValueError("A vectorization job is already running for this table")
            
            # Create new job
            job = VectorizationJob(
                table_config_id=table_config_id,
                status=VectorizationStatus.PENDING,
                created_by=user_id,
                chromadb_collection_name=f"table_{table_config_id}_{table_config.table_name}",
                embedding_model_name="gemini-embedding"
            )
            session.add(job)
            session.flush()
            
            logger.info(f"Created vectorization job {job.id} for table {table_config.table_name}")
            return job
    
    def process_vectorization_job(self, job_id: int) -> bool:
        """
        Process a vectorization job.
        
        Args:
            job_id: ID of the vectorization job
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with get_db_session_context() as session:
                job = session.query(VectorizationJob).get(job_id)
                if not job:
                    raise ValueError("Vectorization job not found")
                
                table_config = session.query(TableConfig).get(job.table_config_id)
                if not table_config:
                    raise ValueError("Table configuration not found")
                
                # Update job status
                job.status = VectorizationStatus.IN_PROGRESS
                job.started_at = datetime.utcnow()
                session.flush()
                
                logger.info(f"Starting vectorization job {job_id} for table {table_config.table_name}")
                
                # Get database connection
                db_conn = table_config.database_connection
                if not db_conn or not db_conn.is_active:
                    raise ValueError("Database connection is not available")
                
                # Process the table
                total_processed, total_successful, total_failed = self._process_table(
                    job, table_config, db_conn.connection_string, session
                )
                
                # Update job completion
                job.status = VectorizationStatus.COMPLETED
                job.completed_at = datetime.utcnow()
                job.total_rows = total_processed
                job.processed_rows = total_processed
                job.successful_rows = total_successful
                job.failed_rows = total_failed
                job.progress_percentage = 100.0
                
                # Update table config
                table_config.last_vectorized = datetime.utcnow()
                table_config.vectorized_records = total_successful
                
                session.flush()
                logger.info(f"Completed vectorization job {job_id}: {total_successful}/{total_processed} records")
                return True
                
        except Exception as e:
            logger.error(f"Error processing vectorization job {job_id}: {e}")
            
            # Update job with error status
            with get_db_session_context() as session:
                job = session.query(VectorizationJob).get(job_id)
                if job:
                    job.status = VectorizationStatus.FAILED
                    job.error_message = str(e)
                    job.completed_at = datetime.utcnow()
                    session.flush()
            
            return False
    
    def _process_table(
        self, 
        job: VectorizationJob, 
        table_config: TableConfig, 
        connection_string: str,
        session
    ) -> Tuple[int, int, int]:
        """
        Process all records in a table.
        
        Args:
            job: Vectorization job
            table_config: Table configuration
            connection_string: Database connection string
            session: Database session
            
        Returns:
            Tuple of (total_processed, successful, failed)
        """
        total_processed = 0
        successful = 0
        failed = 0
        
        # Create database engine
        engine = create_engine(connection_string)
        
        try:
            # Get vectorizable columns
            vectorizable_columns = (
                session.query(ColumnConfig)
                .filter(ColumnConfig.table_config_id == table_config.id)
                .filter(ColumnConfig.should_vectorize == True)
                .all()
            )
            
            if not vectorizable_columns:
                logger.warning(f"No vectorizable columns found for table {table_config.table_name}")
                return 0, 0, 0
            
            # Create ChromaDB collection for this table
            collection_name = job.chromadb_collection_name
            if collection_name:
                self._ensure_collection_exists(collection_name)
                
                # Process records in batches
                for batch in self._get_table_batches(engine, table_config, vectorizable_columns):
                    batch_successful, batch_failed = self._process_batch(
                        batch, table_config, vectorizable_columns, collection_name
                    )
                    successful += batch_successful
                    failed += batch_failed
                    total_processed += len(batch)
                    
                    # Update job progress
                    job.processed_rows = total_processed
                    job.successful_rows = successful
                    job.failed_rows = failed
                    if job.total_rows > 0:
                        job.progress_percentage = (total_processed / job.total_rows) * 100
                    session.flush()
                    
                    logger.info(f"Job {job.id}: Processed {total_processed} records ({successful} successful, {failed} failed)")
            else:
                logger.warning(f"No ChromaDB collection name configured for job {job.id}")
        
        finally:
            engine.dispose()
        
        return total_processed, successful, failed
    
    def _get_table_batches(
        self, 
        engine: Engine, 
        table_config: TableConfig, 
        columns: List[ColumnConfig]
    ) -> Generator[List[Dict[str, Any]], None, None]:
        """
        Get records from the table in batches.
        
        Args:
            engine: Database engine
            table_config: Table configuration
            columns: List of columns to include
            
        Yields:
            Batches of records
        """
        # Build SELECT query
        column_names = [col.column_name for col in columns]
        if table_config.primary_key_column:
            column_names.append(table_config.primary_key_column)
        
        # Add metadata columns
        if table_config.metadata_columns:
            for meta_col in table_config.metadata_columns:
                if meta_col not in column_names:
                    column_names.append(meta_col)
        
        select_columns = ", ".join(column_names)
        base_query = f"SELECT {select_columns} FROM {table_config.table_name}"
        
        # Add WHERE clause if specified
        if table_config.where_clause:
            base_query += f" WHERE {table_config.where_clause}"
        
        # Add ORDER BY for consistent pagination
        if table_config.primary_key_column:
            base_query += f" ORDER BY {table_config.primary_key_column}"
        
        offset = 0
        
        with engine.connect() as conn:
            while True:
                # Get batch
                query = f"{base_query} LIMIT {self.batch_size} OFFSET {offset}"
                result = conn.execute(text(query))
                rows = result.fetchall()
                
                if not rows:
                    break
                
                # Convert to dictionaries
                batch = []
                for row in rows:
                    record = dict(zip(result.keys(), row))
                    batch.append(record)
                
                yield batch
                offset += len(batch)
    
    def _process_batch(
        self, 
        batch: List[Dict[str, Any]], 
        table_config: TableConfig, 
        columns: List[ColumnConfig],
        collection_name: str
    ) -> Tuple[int, int]:
        """
        Process a batch of records.
        
        Args:
            batch: List of database records
            table_config: Table configuration
            columns: List of vectorizable columns
            collection_name: ChromaDB collection name
            
        Returns:
            Tuple of (successful, failed) counts
        """
        successful = 0
        failed = 0
        
        documents = []
        metadatas = []
        ids = []
        
        for record in batch:
            try:
                # Generate content for embedding
                content = self._generate_content(record, table_config, columns)
                if not content:
                    failed += 1
                    continue
                
                # Generate metadata
                metadata = self._generate_metadata(record, table_config)
                
                # Generate unique ID
                record_id = self._generate_record_id(record, table_config)
                
                documents.append(content)
                metadatas.append(metadata)
                ids.append(record_id)
                
            except Exception as e:
                logger.warning(f"Error processing record: {e}")
                failed += 1
        
        # Store batch in ChromaDB
        if documents:
            try:
                self._store_batch_in_chromadb(collection_name, documents, metadatas, ids)
                successful = len(documents)
            except Exception as e:
                logger.error(f"Error storing batch in ChromaDB: {e}")
                failed += len(documents)
                successful = 0
        
        return successful, failed
    
    def _generate_content(
        self, 
        record: Dict[str, Any], 
        table_config: TableConfig, 
        columns: List[ColumnConfig]
    ) -> str:
        """
        Generate content text for embedding based on vectorization strategy.
        
        Args:
            record: Database record
            table_config: Table configuration
            columns: List of vectorizable columns
            
        Returns:
            Content text for embedding
        """
        strategy = table_config.vectorization_strategy
        
        if strategy == VectorizationStrategy.SINGLE_COLUMN:
            # Use the first vectorizable column
            for column in columns:
                if column.should_vectorize:
                    value = record.get(column.column_name)
                    if value is not None:
                        return str(value)[:self.max_text_length]
            return ""
        
        elif strategy == VectorizationStrategy.CONCATENATED:
            # Concatenate all vectorizable columns
            parts = []
            for column in columns:
                if column.should_vectorize:
                    value = record.get(column.column_name)
                    if value is not None:
                        parts.append(f"{column.column_name}: {value}")
            
            content = " | ".join(parts)
            return content[:self.max_text_length]
        
        elif strategy == VectorizationStrategy.WEIGHTED_COMBINATION:
            # Weight columns by their embedding weight
            weighted_parts = []
            for column in columns:
                if column.should_vectorize and column.embedding_weight > 0:
                    value = record.get(column.column_name)
                    if value is not None:
                        # Repeat content based on weight (simple approach)
                        weight_multiplier = max(1, int(column.embedding_weight * 3))
                        weighted_content = " ".join([str(value)] * weight_multiplier)
                        weighted_parts.append(f"{column.column_name}: {weighted_content}")
            
            content = " | ".join(weighted_parts)
            return content[:self.max_text_length]
        
        else:
            # Default: concatenated
            return self._generate_content(record, table_config, columns)
    
    def _generate_metadata(self, record: Dict[str, Any], table_config: TableConfig) -> Dict[str, str | int | float | bool]:
        """
        Generate metadata for the record.
        
        Args:
            record: Database record
            table_config: Table configuration
            
        Returns:
            Metadata dictionary compatible with ChromaDB
        """
        metadata = {
            'table_name': str(table_config.table_name),
            'database_id': int(table_config.database_connection_id),
            'vectorization_strategy': str(table_config.vectorization_strategy),
            'vectorized_at': datetime.utcnow().isoformat()
        }
        
        # Add primary key
        if table_config.primary_key_column:
            pk_value = record.get(table_config.primary_key_column)
            if pk_value is not None:
                metadata['primary_key'] = str(pk_value)
        
        # Add metadata columns
        if table_config.metadata_columns:
            for meta_col in table_config.metadata_columns:
                value = record.get(meta_col)
                if value is not None:
                    metadata[f"meta_{meta_col}"] = str(value)
        
        return metadata
    
    def _generate_record_id(self, record: Dict[str, Any], table_config: TableConfig) -> str:
        """
        Generate a unique ID for the record.
        
        Args:
            record: Database record
            table_config: Table configuration
            
        Returns:
            Unique record ID
        """
        if table_config.primary_key_column:
            pk_value = record.get(table_config.primary_key_column)
            if pk_value is not None:
                return f"{table_config.table_name}_{pk_value}"
        
        # Fallback: hash the record content
        content = json.dumps(record, sort_keys=True, default=str)
        hash_object = hashlib.md5(content.encode())
        return f"{table_config.table_name}_{hash_object.hexdigest()}"
    
    def _ensure_collection_exists(self, collection_name: str):
        """
        Ensure a ChromaDB collection exists for the table.
        
        Args:
            collection_name: Name of the collection
        """
        try:
            # Try to get the collection
            if self.chroma_cache.client:
                self.chroma_cache.client.get_collection(collection_name)
        except Exception:
            # Collection doesn't exist, create it
            if self.chroma_cache.client:
                self.chroma_cache.client.create_collection(
                name=collection_name,
                metadata={"description": f"Vectorized content from database table"}
            )
            logger.info(f"Created ChromaDB collection: {collection_name}")
    
    def _store_batch_in_chromadb(
        self, 
        collection_name: str, 
        documents: List[str], 
        metadatas: List[Dict[str, str | int | float | bool]], 
        ids: List[str]
    ):
        """
        Store a batch of documents in ChromaDB.
        
        Args:
            collection_name: ChromaDB collection name
            documents: List of document texts
            metadatas: List of metadata dictionaries
            ids: List of unique IDs
        """
        collection = None
        if self.chroma_cache.client:
            collection = self.chroma_cache.client.get_collection(collection_name)
        
        # Generate embeddings
        embeddings = []
        for doc in documents:
            embedding = self.embedding_model.embed_documents([doc])[0]
            embeddings.append(embedding)
        
        # Store in ChromaDB
        if collection:
            collection.add(
            documents=documents,
            metadatas=cast(Any, metadatas),  # Type cast for ChromaDB compatibility
            ids=ids,
            embeddings=embeddings
        )
    
    def search_vectorized_content(
        self, 
        query: str, 
        collection_name: Optional[str] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search vectorized content using similarity search.
        
        Args:
            query: Search query
            collection_name: Optional specific collection to search
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of search results
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.embed_documents([query])[0]
            
            if collection_name:
                collections = [collection_name]
            else:
                # Search all collections
                if not self.chroma_cache.client:
                    return []
                collections = [col.name for col in self.chroma_cache.client.list_collections()]
            
            all_results = []
            
            for coll_name in collections:
                try:
                    if not self.chroma_cache.client:
                        continue
                    collection = self.chroma_cache.client.get_collection(coll_name)
                    results = collection.query(
                        query_embeddings=[query_embedding],
                        n_results=top_k,
                        include=['metadatas', 'documents', 'distances']
                    )
                    
                    # Process results (check for None to handle empty collections)
                    if results:
                        documents_list = cast(Any, results.get('documents'))
                        metadatas_list = cast(Any, results.get('metadatas'))
                        distances_list = cast(Any, results.get('distances'))
                        
                        if (documents_list and metadatas_list and distances_list and
                            len(documents_list) > 0 and documents_list[0]):
                            
                            documents = documents_list[0]
                            metadatas = metadatas_list[0] or []
                            distances = distances_list[0] or []
                            
                            for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances)):
                                similarity = 1 - distance  # Convert distance to similarity
                                if similarity >= similarity_threshold:
                                    all_results.append({
                                        'content': doc,
                                'metadata': metadata,
                                'similarity': similarity,
                                'collection': coll_name
                            })
                
                except Exception as e:
                    logger.warning(f"Error searching collection {coll_name}: {e}")
            
            # Sort by similarity and return top results
            all_results.sort(key=lambda x: x['similarity'], reverse=True)
            return all_results[:top_k]
            
        except Exception as e:
            logger.error(f"Error searching vectorized content: {e}")
            return []
    
    def get_job_status(self, job_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the status of a vectorization job.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job status information or None if not found
        """
        with get_db_session_context() as session:
            job = session.query(VectorizationJob).get(job_id)
            if not job:
                return None
            
            return {
                'id': job.id,
                'status': job.status,
                'progress_percentage': job.progress_percentage,
                'total_rows': job.total_rows,
                'processed_rows': job.processed_rows,
                'successful_rows': job.successful_rows,
                'failed_rows': job.failed_rows,
                'started_at': job.started_at.isoformat() if job.started_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                'error_message': job.error_message,
                'collection_name': job.chromadb_collection_name
            }