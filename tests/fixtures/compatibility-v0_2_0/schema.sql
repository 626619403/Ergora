-- Synthetic fixture schema captured from Ergora 0.2.0, before ordered migrations.
CREATE TABLE agent_runs (
                id TEXT PRIMARY KEY, project TEXT NOT NULL, document TEXT NOT NULL);
CREATE TABLE drafts (project TEXT,id TEXT,document TEXT,PRIMARY KEY(project,id));
CREATE TABLE evaluation_suites (project TEXT, digest TEXT, document TEXT, PRIMARY KEY(project,digest));
CREATE TABLE evaluations (id TEXT PRIMARY KEY, project TEXT, document TEXT);
CREATE TABLE kernel_runs (id TEXT PRIMARY KEY, project TEXT, document TEXT);
CREATE TABLE memories (
            project TEXT, id TEXT, revision INTEGER, document TEXT NOT NULL,
            PRIMARY KEY(project, id, revision));
CREATE TABLE memory_mirrors (
            project TEXT, endpoint TEXT, id TEXT, revision INTEGER, binding TEXT NOT NULL,
            PRIMARY KEY(project, endpoint, id));
CREATE TABLE optimizations (id TEXT PRIMARY KEY, project TEXT, document TEXT);
CREATE TABLE projects (id TEXT PRIMARY KEY, document TEXT NOT NULL);
CREATE TABLE research_proposals (id TEXT PRIMARY KEY,project TEXT,document TEXT);
CREATE TABLE research_runs (id TEXT PRIMARY KEY,project TEXT,cancel INTEGER,document TEXT);
CREATE TABLE skill_events (project TEXT, name TEXT, document TEXT);
CREATE TABLE skill_heads (project TEXT, name TEXT, digest TEXT, revision INTEGER, PRIMARY KEY(project,name));
CREATE TABLE skill_versions (project TEXT, digest TEXT, document TEXT, PRIMARY KEY(project,digest));
CREATE TABLE source_heads (project TEXT,url TEXT,sha TEXT,PRIMARY KEY(project,url));
CREATE TABLE source_snapshots (project TEXT,url TEXT,sha TEXT,document TEXT,PRIMARY KEY(project,url,sha));
