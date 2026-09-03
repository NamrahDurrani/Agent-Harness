# AgriBot-Agentic RAG Pipeline for Agricultural Knowledge Base

An agentic Retrieval-Augmented Generation (RAG) system for answering natural-language questions over a mixed corpus of agricultural documents, including digitally generated and fully scanned PDFs. The system combines adaptive PDF extraction, hybrid retrieval, evidence evaluation, retry-based query refinement, web fallback, claim verification, and structured execution logging.

## Architecture

```text
                         User Query
                             |
                             v
                  +---------------------+
                  | Conversation History|
                  +----------+----------+
                             |
                             v
                  +---------------------+
                  |  Query Rewriter     |
                  |       (LLM)         |
                  +----------+----------+
                             |
                             v
                  +---------------------+
                  |    Orchestrator     |
                  |       (LLM)         |
                  +----------+----------+
                             |
                 +-----------+-----------+
                 |                       |
              Direct                    RAG
                 |                       |
                 |                       v
                 |              +----------------+
                 |              | Hybrid         |
                 |              | Retrieval      |
                 |              | Vector + BM25   |
                 |              +-------+--------+
                 |                      |
                 |                      v
                 |              +----------------+
                 |              | RRF Reranking  |
                 |              +-------+--------+
                 |                      |
                 |                      v
                 |              +----------------+
                 |              | Relevance      |
                 |              | Evaluator      |
                 |              | (LLM)          |
                 |              +-------+--------+
                 |                      |
                 |              +-------+-------+
                 |              |               |
                 |          Sufficient/       None
                 |          Partial             |
                 |              |               v
                 |              |        Retry / Web
                 |              |               |
                 |              +-------+-------+
                 |                      |
                 +----------------------+
                             |
                             v
                       Final Answer
                             |
                             v
                  Structured Execution Log
```

## What Makes It Agentic?

The system is more than a fixed retrieve-then-generate pipeline:

* **Query Rewriter** uses conversation context to reformulate the user's query.
* **Orchestrator** determines whether retrieval is required.
* **Relevance Evaluator** checks whether retrieved evidence is sufficient before generation.
* **Retry Controller** can trigger query refinement and another retrieval attempt when evidence is inadequate.
* **Web Fallback** provides additional research when the internal agricultural knowledge base cannot provide sufficient evidence.
* **Claim Verification** checks evidence supporting important claims before the final response.
* **Execution Logging** records the major decisions and intermediate steps for debugging and auditing.

The system therefore follows a **retrieve → evaluate → retry/research → verify → answer** pattern rather than blindly generating an answer from the first retrieved results.

---

## Adaptive PDF Processing

The agricultural corpus contains both digitally generated and scanned documents.

| Document type | Processing                   |
| ------------- | ---------------------------- |
| Digital PDF   | PyMuPDF text extraction      |
| Scanned PDF   | Tesseract OCR                |
| Mixed PDF     | Adaptive extraction per page |

Extraction is performed **per page**. Direct text extraction is attempted first; when insufficient text is detected, the page is rasterized and processed with OCR. This allows a single PDF to contain both searchable and scanned pages without requiring a document-level assumption.

---

## Hybrid Retrieval

The retrieval layer combines two complementary approaches:

```text
                    User Query
                        |
              +---------+---------+
              |                   |
              v                   v
        Vector Search          BM25 Search
          ChromaDB              Sparse
              |                   |
              +---------+---------+
                        |
                        v
                   RRF Fusion
                        |
                        v
                  Ranked Evidence
```

### Vector Retrieval

Uses local `sentence-transformers` embeddings to identify semantically related passages.

### BM25 Retrieval

Provides lexical retrieval for exact terminology, names, locations, policies, diseases, organizations, and other keyword-sensitive queries.

### RRF Fusion

Reciprocal Rank Fusion combines both retrieval rankings before evidence evaluation.

---

## Evidence Evaluation

Retrieved documents are not automatically treated as sufficient evidence.

The **Relevance Evaluator** classifies the retrieved context as:

```text
sufficient
partial
none
```

If evidence is insufficient, the system can refine the query and retry retrieval. After the retry limit is reached, the system can fall back to web research or return an evidence-aware response instead of fabricating an answer.

---

## Web Research and Verification

When the internal knowledge base cannot sufficiently answer a question, the pipeline can use web research to obtain additional evidence.

The resulting information can then pass through claim verification before being used in the final answer.

This is particularly important for information that may be:

* outside the local agricultural corpus
* historical
* organization/company related
* policy related
* newly published or changing
* insufficiently represented in the local KB

---

# Agent Harness for Document Generation

The Agent Harness is an additional orchestration layer designed **specifically for document-generation requests**.

It is intentionally separated from the normal conversational RAG path. A normal question such as:

> "What wheat diseases are monitored in Punjab?"

continues through the existing RAG pipeline.

A request such as:

> "Generate a detailed PDF report on wheat diseases."

activates the document-generation Harness.

```text
                         User Request
                              |
                              v
                   TaskExecutionSupervisor
                              |
                    Is this a document?
                       /             \
                     NO               YES
                     |                 |
                     v                 v
               Existing RAG      Document Harness
                                   |
                     +-------------+-------------+
                     |                           |
                     v                           v
            Research Supervisor         Document Supervisor
                     |                           |
             +-------+-------+           +-------+-------+
             |       |       |           |       |       |
             v       v       v           v       v       v
         Retrieval Reranker Web       Author  Coding    QA
             |               |
             +-------+-------+
                     |
                     v
             Claim Verification
                     |
                     v
              Research Package
                     |
                     v
             Document Generation
                     |
                     v
              Artifact Validation
                     |
                     v
              PDF / DOCX / TXT /
                CSV / Markdown
```

## Harness Responsibilities

The document Harness is responsible for coordinating the document workflow rather than replacing the existing RAG components.

### TaskExecutionSupervisor

Determines whether the request requires document generation and coordinates the document workflow.

### Research Supervisor

Coordinates the existing knowledge-retrieval and research components:

* Vector retrieval
* BM25 retrieval
* RRF reranking
* Web research
* Claim verification

Its goal is to produce a sufficiently supported **Research Package** for the document.

### Document Supervisor

Coordinates document production:

* document planning
* content authoring
* structured data/code generation where required
* artifact generation
* document QA

### Research → Document Integration

The two branches meet through a structured research result:

```text
Research Supervisor
        |
        v
   Research Package
        |
        v
Document Supervisor
        |
        v
Requested Artifact
```

This separation allows the system to distinguish between:

```text
Researching what should be written
```

and:

```text
Producing the requested document
```

while retaining the existing retrieval and verification infrastructure.

## Current Harness Goal

The Harness is being developed to make document generation more reliable and more detailed by introducing:

* task-level planning before execution
* agriculture-domain-aware research planning
* separation of research and document generation
* evidence-aware document writing
* support for multiple document formats
* artifact validation
* document-level QA
* execution tracing for the live UI

The Harness is **not intended to replace the existing conversational RAG pipeline**. Its scope is document-generation workflows, where additional planning, research, generation, validation, and artifact handling are required.
