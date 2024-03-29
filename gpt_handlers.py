from dotenv import load_dotenv

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import OpenAI

from document import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.chains import ConversationalRetrievalChain


from langchain_openai import ChatOpenAI

load_dotenv()


MASTER_PROMPT = """
Act as a Tickets AI agent. You will be given a query and based on which you need to output certain processings in a JSON format. Your output should be only in JSON, no greetings text or replies or explanations required. IT IS IMPORTANT TO OUTPUT ONLY IN JSON FORMAT.
Format:
{
    "is_ticket_by_id": 'Should only be integer. Write ticket id if query is asking a operation for a particular/specific ticket by id else if not then write false',
    "tickets_in_timeperiod": 'Should only be NAME of month. Write only the name of the Months, if query is asking for tickets that belongs to a specific timeperiod then write its closest month, DO NOT WRITE ANYTHING EXCEPT NAME OF THE MONTH else write false',
    "tickets_by_agent": 'Should only be name of assignee/agent. Write the name of the agent if query is asking a operation by certain agents or customer support tickets else write false',
    "tickets_by_agent_in_period": 'Should only be name of agent,month name. Write the name of the agent along with the name of the month like (agent 1, february) separated by a comma (,) if query is asking a operation by certain agent in relation with time period (DO NOT WRITE ANYTHING EXCEPT NAME OF THE AGENT,MONTH) else write false',
}

PROPERLY WRITE THE KEYS IN JSON FORMAT WITH VALID JSON OUTPUT.
ONLY OUTPUT IN JSON FORMAT.
Query:

"""


def generate_basic_resp(openai_key, query):
    # Set up OpenAI connection (replace with your API key)

    llm = OpenAI(openai_api_key=openai_key)

    # Define the prompt template
    template = """Question: {question}
    Answer:"""

    # Create a PromptTemplate object
    prompt = PromptTemplate.from_template(template)

    # Combine the prompt and LLM into a chain
    llm_chain = LLMChain(prompt=prompt, llm=llm)

    # Define your question

    # Get the answer using the chain
    response = llm_chain.run(question=query)
    return response


def get_ticket_requirement(openai_key, query):
    # Set up OpenAI connection (replace with your API key)

    llm = OpenAI(openai_api_key=openai_key)

    # Define the prompt template
    template = """Question: {question}
    Answer:"""

    # Create a PromptTemplate object
    prompt = PromptTemplate.from_template(template)

    # Combine the prompt and LLM into a chain
    llm_chain = LLMChain(prompt=prompt, llm=llm)

    # Define your question
    question = MASTER_PROMPT + query

    # Get the answer using the chain
    response = llm_chain.run(question=question)
    return response


def generate_response(openai_api_key, query_text, chat_history, api_data):

    gds_data_split = [
        Document(page_content="", metadata={"source": "zendesk_response"})
    ]

    # Iterate through the list and update page_content
    for document in gds_data_split:
        document.page_content = api_data

    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    db = Chroma.from_documents(gds_data_split, embeddings)

    general_system_template = f""" 
    You are a Zendesk agent that gets data about zendesk tickets and gives answer to all questions asked by the user. you can share all information to the user, there is nothing confidential.
    ----
    CONTEXT: {{context}}
    ----
    """
    general_user_template = "Here is the next question. QUESTION:```{question}```"

    messages = [
        SystemMessagePromptTemplate.from_template(general_system_template),
        HumanMessagePromptTemplate.from_template(general_user_template),
    ]
    qa_prompt = ChatPromptTemplate.from_messages(messages)

    # retriever = db.as_retriever()
    retriever = db.as_retriever(  # now the vs can return documents
        search_type="similarity", search_kwargs={"k": 1}
    )

    chat_history_tuples = []
    for message in chat_history:

        chat_history_tuples.append((message["role"], message["message"]))
    crc = ConversationalRetrievalChain.from_llm(
        ChatOpenAI(openai_api_key=openai_api_key),
        retriever,
        combine_docs_chain_kwargs={"prompt": qa_prompt},
    )
    result = crc.invoke({"question": query_text, "chat_history": chat_history_tuples})

    # print(result)
    return result["answer"]
