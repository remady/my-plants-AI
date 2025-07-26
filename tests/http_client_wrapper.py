"""HTTP client wrapper for testing chat and document API endpoints.

This module provides the HttpClientWrapper class for interacting with chat and document-related endpoints using an AsyncClient session.
"""

from os import PathLike
from httpx import AsyncClient, HTTPStatusError

from pydantic import TypeAdapter

from app.schemas.auth import SessionResponse, TokenResponse
from app.schemas.chat import ChatRequest, ChatResponse, ChatResponseDebug, Message
from app.schemas.document import DocumentResponse
from app.utils.graph import dump_messages
from app.core.config import settings
from app.core.logging import logger


documents_list_adapter = TypeAdapter(list[DocumentResponse])


class HttpClientWrapper:
    """HTTP client wrapper for interacting with chat and document API endpoints.

    Attributes.
    ----------
    session : AsyncClient
        The HTTPX async client session.
    base_url : str
        The base URL for API requests.

    Methods.
    -------
    chat(messages: list[Message]) -> list[Message]
        Send chat messages.
    chat_stream(prompt: str)
        Stream chat responses.
    list_chat_messages()
        List chat messages.
    delete_chat_messages()
        Delete chat messages.
    upload_document(file_path: str)
        Upload a document.
    list_documents()
        List documents.
    delete_document()
        Delete a document.
    """

    def __init__(self, session: AsyncClient, base_url: str = None):
        """Initialize the HttpClientWrapper with an AsyncClient session and a base URL.

        Args:
            session (AsyncClient): The HTTPX async client session.
            base_url (str): The base URL for API requests.
        """
        self.session = session
        if base_url:
            self.session.base_url = base_url
            
    def __repr__(self):
        return "<HttpClientWrapper>"

    async def _get_login_access_token(self, username: str, password: str) -> TokenResponse:
        """Authenticate the user and return an access token.

        Parameters
        ----------
        username : str
            The username for authentication.
        password : str
            The password for authentication.

        Returns:
        -------
        str
            The access token received after successful authentication.

        Raises:
        ------
        httpx.HTTPStatusError
            If the response status is not successful.
        """
        logger.info("get_login_access_token")
        resp_login = await self.session.post(
            "/auth/login", data={"username": username, "password": password, "grant_type": "password"}
        )
        resp_login.raise_for_status()
        token = TokenResponse.model_validate(resp_login.json())
        return token

    async def create_chat_session(self, username: str, password: str) -> SessionResponse:
        """Create a new chat session by authenticating the user and updating the session headers.

        Parameters
        ----------
        username : str
            The username for authentication.
        password : str
            The password for authentication.

        Returns:
        -------
        SessionResponse
            The session response containing the access token.

        Raises:
        ------
        httpx.HTTPStatusError
            If the authentication or session creation fails.
        """
        logger.info("create_chat_session")
        token = await self._get_login_access_token(username=username, password=password)
        session_resp = await self.session.post(
            "/auth/session", headers={"Authorization": f"Bearer {token.access_token}"}
        )
        session_resp.raise_for_status()
        session = SessionResponse.model_validate(session_resp.json())
        self.session.headers.update({"Authorization": f"Bearer {session.token.access_token}"})
        return session

    async def chat(self, chat_request: ChatRequest) -> ChatResponse:
        """Send chat messages to the /chat endpoint and return the chat response.

        Parameters.
        ----------
        messages : list[Message]
            The list of chat messages to send.

        Returns:
        -------
        ChatResponse
            The validated chat response from the API.

        Raises:
        ------
        httpx.HTTPStatusError
            If the response status is not successful.
        Exception
            If there is an error parsing the response JSON.
        """
        logger.info("chat")
        assert isinstance(chat_request, ChatRequest), "[chat_request] param should be type of <ChatRequest>"
        response = await self.session.post(
            "/chatbot/chat", 
            json=chat_request.model_dump()
        )
        response.raise_for_status()
        response_json = response.json()
        return ChatResponse.model_validate(response_json)

    async def list_chat_messages_debug(self) -> ChatResponseDebug:
        """Retrieve the list of chat messages from the /chatbot/messages endpoint.

        Returns:
        -------
        ChatResponseDebug
            The validated chat response from the API.

        Raises:
        ------
        httpx.HTTPStatusError
            If the response status is not successful.
        """
        logger.info("list_chat_messages_debug")
        response = await self.session.get("/testing/messages")
        response.raise_for_status()
        response_json = response.json()
        return ChatResponseDebug.model_validate(response_json)


    async def delete_chat_messages(self) -> str:
        """Delete all chat messages from the /chatbot/messages endpoint.

        Returns:
        -------
        str
            The response text from the API.

        Raises:
        ------
        httpx.HTTPStatusError
            If the response status is not successful.
        """
        logger.info("delete_chat_messages")
        response = await self.session.delete("/chatbot/messages")
        response.raise_for_status()
        return response.text
    
    async def get_graph_trajectory(self) -> dict:
        """Retrieve the graph trajectory from the /testing/graph-trajectory endpoint.

        Returns:
        -------
        dict
            The JSON response containing the graph trajectory.

        Raises:
        ------
        httpx.HTTPStatusError
            If the response status is not successful.
        Exception
            If there is an error parsing the response JSON.
        """
        logger.info("get_graph_trajectory")
        response = await self.session.get("/testing/graph-trajectory")
        response.raise_for_status()
        try:
            return response.json()
        except Exception as e:
            logger.error("get_graph_trajectory_failed", error=str(e), exc_info=True)
            raise e

    async def upload_document(self, file_path: PathLike) -> DocumentResponse:
        """Upload a document to the /documents/upload endpoint.

        Parameters
        ----------
        file_path : PathLike
            The path to the document file to upload.

        Returns:
        -------
        bool
            True if the document was uploaded successfully.

        Raises:
        ------
        httpx.HTTPStatusError
            If the response status is not successful.
        """
        logger.info("upload_document", document=file_path)
        document = {"document": open(file_path, "rb")}
        resp = await self.session.post("/documents/upload", files=document)
        resp.raise_for_status()
        return DocumentResponse.model_validate(resp.json())

    async def list_documents(self) -> list[DocumentResponse]:
        """Retrieve the list of documents from the /documents endpoint.

        Returns:
        -------
        list[DocumentResponse]
            The validated list of document responses from the API.

        Raises:
        ------
        httpx.HTTPStatusError
            If the response status is not successful.
        Exception
            If there is an error parsing the response JSON.
        """
        logger.info("list_documents")
        documents_resp = await self.session.get("/documents")
        documents_resp.raise_for_status()
        documents = documents_list_adapter.validate_python(documents_resp.json())
        return documents

    async def delete_document(self, document_id: str) -> bool:
        """Delete a document by its ID from the /documents endpoint.

        Parameters
        ----------
        document_id : str
            The ID of the document to delete.

        Returns:
        -------
        bool
            True if the document was deleted successfully, False otherwise.

        Raises:
        ------
        httpx.HTTPStatusError
            If the response status is not successful and not handled.
        """
        logger.info("delete_document")
        delete_resp = await self.session.delete(f"/documents/{document_id}")
        delete_resp.raise_for_status()
        delete_resp_json = delete_resp.json()
        return "status" in delete_resp_json and delete_resp_json.get("status", "").lower() == "ok"

    async def close(self) -> None:
        """Close the underlying HTTPX async client session.

        This method should be called to properly release resources held by the session.
        """
        logger.info("close_session")
        await self.session.aclose()
