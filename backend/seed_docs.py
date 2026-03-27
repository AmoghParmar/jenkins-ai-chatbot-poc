"""
Seeds the ChromaDB vector store with 15 curated Jenkins Q&A pairs
and additional doc chunks. Run this once before starting the server.

Usage:
    python -m backend.seed_docs
    # or
    python backend/seed_docs.py
"""

import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import chromadb
from chromadb.utils import embedding_functions

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "..", "chroma_db")
COLLECTION_NAME = "jenkins_docs"

_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

# ── Document corpus ──────────────────────────────────────────────────────────
DOCS = [
    # ── Docker agent ──────────────────────────────────────────────────────
    {
        "id": "docker-agent-1",
        "content": (
            "To use a Docker agent in a Declarative Pipeline, add an `agent` block "
            "with `docker { image 'node:20' }`. Example:\n\n"
            "```groovy\npipeline {\n  agent { docker { image 'maven:3.9-eclipse-temurin-21' } }\n"
            "  stages {\n    stage('Build') {\n      steps { sh 'mvn clean install' }\n    }\n  }\n}\n```\n"
            "The Docker plugin must be installed and the Jenkins agent must have Docker available."
        ),
        "url": "https://www.jenkins.io/doc/book/pipeline/docker/",
        "category": "pipeline",
        "question": "How do I add a Docker agent to my pipeline?",
    },
    {
        "id": "docker-agent-2",
        "content": (
            "Docker agents require the 'Docker Pipeline' plugin. Install it from "
            "Manage Jenkins → Plugins → Available. The agent node must have Docker "
            "installed and the `jenkins` user must be in the `docker` group: "
            "`sudo usermod -aG docker jenkins`. Restart Jenkins afterwards."
        ),
        "url": "https://plugins.jenkins.io/docker-workflow/",
        "category": "pipeline",
        "question": "Why is my Docker agent failing?",
    },
    # ── Declarative Pipeline ───────────────────────────────────────────────
    {
        "id": "declarative-1",
        "content": (
            "A Declarative Pipeline is defined in a `Jenkinsfile` with a `pipeline {}` block. "
            "It has three required sections: `agent` (where to run), `stages` (what to run), "
            "and `steps` (the actual commands). Example:\n\n"
            "```groovy\npipeline {\n  agent any\n  stages {\n    stage('Test') {\n"
            "      steps { sh 'npm test' }\n    }\n  }\n}\n```"
        ),
        "url": "https://www.jenkins.io/doc/book/pipeline/syntax/",
        "category": "pipeline",
        "question": "What is a Declarative Pipeline?",
    },
    {
        "id": "declarative-2",
        "content": (
            "Freestyle vs Pipeline: Use Freestyle for simple, single-step builds with "
            "no branching logic. Use Pipeline (Declarative or Scripted) when you need "
            "multi-stage builds, parallel stages, Docker agents, or version-controlled "
            "build definitions. Multibranch Pipeline is best for GitHub/GitLab repos "
            "where each branch has its own Jenkinsfile."
        ),
        "url": "https://www.jenkins.io/doc/book/pipeline/getting-started/",
        "category": "pipeline",
        "question": "Should I use Freestyle or Pipeline?",
    },
    # ── Maven pipeline ─────────────────────────────────────────────────────
    {
        "id": "maven-1",
        "content": (
            "For a Maven project, use the Maven Docker image as agent:\n\n"
            "```groovy\npipeline {\n  agent { docker { image 'maven:3.9-eclipse-temurin-21' } }\n"
            "  stages {\n    stage('Build') { steps { sh 'mvn clean package -DskipTests' } }\n"
            "    stage('Test')  { steps { sh 'mvn test' } }\n"
            "    stage('Deploy'){ steps { sh 'mvn deploy' } }\n  }\n}\n```\n"
            "Configure Maven settings via `withMaven()` if you need a custom `settings.xml`."
        ),
        "url": "https://www.jenkins.io/doc/book/pipeline/maven/",
        "category": "pipeline",
        "question": "How do I configure a Maven pipeline?",
    },
    # ── Build failures ─────────────────────────────────────────────────────
    {
        "id": "build-failure-1",
        "content": (
            "To diagnose a build failure: 1) Click the failed build number. "
            "2) Open Console Output - look for 'ERROR' or 'BUILD FAILURE'. "
            "3) Common causes: missing credentials (add in Manage Jenkins → Credentials), "
            "agent offline (check agent status), compilation errors (check the exact "
            "line number in the console), or a flaky test (re-run the stage with "
            "`retry(3) { ... }`)."
        ),
        "url": "https://www.jenkins.io/doc/book/using/using-jenkins/",
        "category": "general",
        "question": "Why did my build fail?",
    },
    {
        "id": "build-failure-2",
        "content": (
            "If a build fails only on the second run but not the first, the likely causes are: "
            "1) Leftover workspace state - add `cleanWs()` at the start of the pipeline. "
            "2) Port conflict from a previous run - kill lingering processes. "
            "3) Cached Docker layer conflict - use `--no-cache` flag. "
            "4) Race condition in parallel stages - add explicit `stage` dependencies."
        ),
        "url": "https://www.jenkins.io/doc/book/pipeline/pipeline-best-practices/",
        "category": "general",
        "question": "Build fails only on second run",
    },
    # ── Credentials ────────────────────────────────────────────────────────
    {
        "id": "credentials-1",
        "content": (
            "To add credentials: Manage Jenkins → Credentials → (global) → Add Credentials. "
            "For a GitHub token, choose 'Secret text'. Use in pipeline:\n\n"
            "```groovy\nwithCredentials([string(credentialsId: 'github-token', variable: 'TOKEN')]) {\n"
            "  sh 'git push https://$TOKEN@github.com/org/repo.git main'\n}\n```\n"
            "Never hardcode secrets in the Jenkinsfile."
        ),
        "url": "https://www.jenkins.io/doc/book/using/using-credentials/",
        "category": "general",
        "question": "How do I set up credentials in Jenkins?",
    },
    {
        "id": "credentials-2",
        "content": (
            "For SSH credentials: add a 'SSH Username with private key' credential in "
            "Manage Jenkins → Credentials. Use the `sshagent` step in your pipeline:\n\n"
            "```groovy\nsshagent(['my-ssh-key']) {\n  sh 'ssh -o StrictHostKeyChecking=no user@host'\n}\n```\n"
            "The SSH Agent plugin must be installed."
        ),
        "url": "https://plugins.jenkins.io/ssh-agent/",
        "category": "general",
        "question": "How do I use SSH keys in Jenkins?",
    },
    # ── Email notifications ────────────────────────────────────────────────
    {
        "id": "email-1",
        "content": (
            "To add email notifications install the 'Email Extension' plugin. "
            "Configure SMTP in Manage Jenkins → Configure System → Extended E-mail Notification. "
            "In pipeline:\n\n"
            "```groovy\npost {\n  failure {\n    emailext(\n      subject: \"Build FAILED: ${env.JOB_NAME}\",\n"
            "      body: 'Check console: ${env.BUILD_URL}',\n      to: 'team@example.com'\n    )\n  }\n}\n```"
        ),
        "url": "https://plugins.jenkins.io/email-ext/",
        "category": "general",
        "question": "How do I add email notification when a build fails?",
    },
    # ── Parallel stages ────────────────────────────────────────────────────
    {
        "id": "parallel-1",
        "content": (
            "Run stages in parallel to speed up builds:\n\n"
            "```groovy\nstage('Tests') {\n  parallel {\n"
            "    stage('Unit')        { steps { sh 'npm run test:unit' } }\n"
            "    stage('Integration') { steps { sh 'npm run test:int' } }\n"
            "    stage('Lint')        { steps { sh 'npm run lint' } }\n  }\n}\n```\n"
            "All parallel branches run simultaneously on available agents."
        ),
        "url": "https://www.jenkins.io/doc/book/pipeline/syntax/#parallel",
        "category": "pipeline",
        "question": "How do I run stages in parallel?",
    },
    # ── Environment variables ──────────────────────────────────────────────
    {
        "id": "envvars-1",
        "content": (
            "Access Jenkins built-in environment variables with `env.VAR_NAME`:\n"
            "- `env.BUILD_NUMBER` - current build number\n"
            "- `env.JOB_NAME` - name of the job\n"
            "- `env.BRANCH_NAME` - branch (Multibranch only)\n"
            "- `env.BUILD_URL` - full URL of the build\n\n"
            "Define custom env vars in the `environment {}` block:\n"
            "```groovy\nenvironment { APP_VERSION = '1.0.0' }\n```"
        ),
        "url": "https://www.jenkins.io/doc/book/pipeline/jenkinsfile/#using-environment-variables",
        "category": "pipeline",
        "question": "How do I use environment variables in Jenkins?",
    },
    # ── JNLP agents ───────────────────────────────────────────────────────
    {
        "id": "jnlp-1",
        "content": (
            "To add a JNLP (inbound) agent: Manage Jenkins → Nodes → New Node. "
            "Set 'Launch method' to 'Launch agent by connecting it to the controller'. "
            "On the agent machine, run:\n\n"
            "```bash\njava -jar agent.jar -url http://jenkins:8080/ \\\n"
            "  -secret <secret> -name my-agent -workDir /home/jenkins/agent\n```\n"
            "Download `agent.jar` from your Jenkins controller at `/jnlpJars/agent.jar`."
        ),
        "url": "https://www.jenkins.io/doc/book/using/using-agents/",
        "category": "general",
        "question": "How do I connect a JNLP agent?",
    },
    # ── Multibranch Pipeline ───────────────────────────────────────────────
    {
        "id": "multibranch-1",
        "content": (
            "A Multibranch Pipeline automatically creates a pipeline job for every branch "
            "and PR in your repository that contains a Jenkinsfile. To set one up: "
            "New Item → Multibranch Pipeline → Add branch source (GitHub/GitLab). "
            "Each branch runs the Jenkinsfile found on that branch. "
            "Stale branches are automatically deleted when they're removed from the repo."
        ),
        "url": "https://www.jenkins.io/doc/book/pipeline/multibranch/",
        "category": "pipeline",
        "question": "What is a Multibranch Pipeline?",
    },
    # ── Plugin installation ────────────────────────────────────────────────
    {
        "id": "plugins-1",
        "content": (
            "To install a plugin: Manage Jenkins → Plugins → Available plugins. "
            "Search by name and click Install. The plugin takes effect after Jenkins restarts. "
            "For automated plugin management, use the Plugin Installation Manager Tool or "
            "define plugins in a `plugins.txt` file for Docker-based setups. "
            "Always pin plugin versions in production to avoid unexpected breaking changes."
        ),
        "url": "https://www.jenkins.io/doc/book/managing/plugins/",
        "category": "general",
        "question": "How do I install a Jenkins plugin?",
    },
]


def seed():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    # Drop and recreate for a clean seed
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=_ef,
        metadata={"hnsw:space": "cosine"},
    )

    ids = [d["id"] for d in DOCS]
    documents = [
        f"Q: {d['question']}\n\nA: {d['content']}" for d in DOCS
    ]
    metadatas = [
        {"url": d["url"], "category": d["category"], "question": d["question"]}
        for d in DOCS
    ]

    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    print(f"✅  Seeded {len(DOCS)} Jenkins doc chunks into ChromaDB at '{CHROMA_PATH}'")
    print("   Run: uvicorn backend.main:app --reload")


if __name__ == "__main__":
    seed()
