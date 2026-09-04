"""Ingest the cupcake store document into Foundry IQ on Azure.

Foundry IQ is the managed knowledge layer in Microsoft Foundry, built on
Azure AI Search. This script builds the full pipeline:

  1. Create a search index (with a semantic configuration).
  2. Chunk the markdown document by section and upload the chunks.
  3. Create a search-index knowledge source over that index.
  4. Create a knowledge base that references the knowledge source.

The resulting knowledge base surfaces in the Microsoft Foundry portal as a
Foundry IQ knowledge base that agents can query with agentic retrieval.

Required environment variables (in .env):
  AZURE_SEARCH_ENDPOINT   e.g. https://<service>.search.windows.net
  AZURE_SEARCH_API_KEY    admin key (optional; falls back to Entra ID login)
"""

import os
import re

from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchFieldDataType,
    SemanticConfiguration,
    SemanticSearch,
    SemanticPrioritizedFields,
    SemanticField,
    SearchIndexKnowledgeSource,
    SearchIndexKnowledgeSourceParameters,
    SearchIndexFieldReference,
    KnowledgeBase,
    KnowledgeSourceReference,
)

DOCUMENT_PATH = "cupcake-store-info.md"
INDEX_NAME = "cupcake-store-index"
SEMANTIC_CONFIG_NAME = "cupcake-semantic"
KNOWLEDGE_SOURCE_NAME = "cupcake-store-ks"
KNOWLEDGE_BASE_NAME = "cupcake-store-kb"


def get_credential():
    """Use an admin key if provided, otherwise fall back to Entra ID."""
    api_key = os.environ.get("AZURE_SEARCH_API_KEY")
    if api_key:
        return AzureKeyCredential(api_key)
    return DefaultAzureCredential()


def chunk_document(path: str) -> list[dict]:
    """Split the markdown document into one chunk per top-level (##) section."""
    with open(path, encoding="utf-8") as f:
        text = f.read()

    # Split on level-2 headings, keeping the heading with its body.
    parts = re.split(r"\n(?=## )", text)
    chunks: list[dict] = []
    for i, part in enumerate(parts):
        body = part.strip()
        if not body:
            continue
        heading = body.splitlines()[0].lstrip("# ").strip()
        chunks.append(
            {
                "id": str(i),
                "title": heading,
                "category": heading,
                "content": body,
            }
        )
    return chunks


def create_index(index_client: SearchIndexClient) -> None:
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
        SearchableField(name="title", type=SearchFieldDataType.String),
        SearchableField(name="category", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SearchableField(name="content", type=SearchFieldDataType.String),
    ]

    semantic_config = SemanticConfiguration(
        name=SEMANTIC_CONFIG_NAME,
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="title"),
            keywords_fields=[SemanticField(field_name="category")],
            content_fields=[SemanticField(field_name="content")],
        ),
    )

    index = SearchIndex(
        name=INDEX_NAME,
        fields=fields,
        semantic_search=SemanticSearch(configurations=[semantic_config]),
    )
    index_client.create_or_update_index(index)
    print(f"Index '{INDEX_NAME}' created or updated.")


def upload_documents(endpoint: str, credential, chunks: list[dict]) -> None:
    search_client = SearchClient(endpoint=endpoint, index_name=INDEX_NAME, credential=credential)
    result = search_client.upload_documents(documents=chunks)
    succeeded = sum(1 for r in result if r.succeeded)
    print(f"Uploaded {succeeded}/{len(chunks)} document chunks.")


def create_knowledge_source(index_client: SearchIndexClient) -> None:
    knowledge_source = SearchIndexKnowledgeSource(
        name=KNOWLEDGE_SOURCE_NAME,
        description="Cupcake store customer information (hours, delivery, returns).",
        search_index_parameters=SearchIndexKnowledgeSourceParameters(
            search_index_name=INDEX_NAME,
            semantic_configuration_name=SEMANTIC_CONFIG_NAME,
            source_data_fields=[
                SearchIndexFieldReference(name="id"),
                SearchIndexFieldReference(name="title"),
                SearchIndexFieldReference(name="category"),
                SearchIndexFieldReference(name="content"),
            ],
            search_fields=[SearchIndexFieldReference(name="content")],
        ),
    )
    index_client.create_or_update_knowledge_source(knowledge_source)
    print(f"Knowledge source '{KNOWLEDGE_SOURCE_NAME}' created or updated.")


def create_knowledge_base(index_client: SearchIndexClient) -> None:
    knowledge_base = KnowledgeBase(
        name=KNOWLEDGE_BASE_NAME,
        description="Foundry IQ knowledge base for the Sparkles Cupcake Store.",
        knowledge_sources=[KnowledgeSourceReference(name=KNOWLEDGE_SOURCE_NAME)],
    )
    index_client.create_or_update_knowledge_base(knowledge_base)
    print(f"Knowledge base '{KNOWLEDGE_BASE_NAME}' created or updated.")


def main() -> None:
    load_dotenv()

    endpoint = os.environ["AZURE_SEARCH_ENDPOINT"]
    credential = get_credential()
    index_client = SearchIndexClient(endpoint=endpoint, credential=credential)

    chunks = chunk_document(DOCUMENT_PATH)
    print(f"Prepared {len(chunks)} chunks from '{DOCUMENT_PATH}'.")

    create_index(index_client)
    upload_documents(endpoint, credential, chunks)
    create_knowledge_source(index_client)
    create_knowledge_base(index_client)

    print(
        f"\nDone. Foundry IQ knowledge base '{KNOWLEDGE_BASE_NAME}' is ready "
        "and will appear in the Microsoft Foundry portal."
    )


if __name__ == "__main__":
    main()
