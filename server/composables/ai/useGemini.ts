import { HumanMessage, SystemMessage } from '@langchain/core/messages'
import { ChatGoogleGenerativeAI } from '@langchain/google-genai'

export function useGemini() {
  const gemini = new ChatGoogleGenerativeAI({
    model: 'gemini-2.0-flash',
    temperature: 0,
  })

  function sendMessage(message: string) {
    return gemini.invoke([
      // Text to SQL conversion prompt
      new SystemMessage(
        'You are a helpful assistant that translates natural language to SQL queries. Only provide the SQL query as output, without any additional text or explanation.',
      ),
      new HumanMessage(message),
    ])
  }

  return { sendMessage }
}
