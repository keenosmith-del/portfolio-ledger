import { Badge, Table, Pager, Panel } from "./components/Workspace";
import {
  useCallback,
  useEffect,
  useState,
  type FormEvent,
  type ReactNode,
} from "react";
import {
  Activity,
  ArrowDownToLine,
  ArrowRight,
  BookOpen,
  Building2,
  Check,
  CircleHelp,
  FileCheck2,
  History,
  Layers3,
  LayoutDashboard,
  LogOut,
  RefreshCw,
  Search,
  ShieldCheck,
  SlidersHorizontal,
  Upload,
  X,
} from "lucide-react";
import {
  api,
  post,
  setIdentity,
  type Identity,
  type Portfolio,
  type Overview,
  type Page,
  type Job,
  type Lease,
  type Ledger,
  type ExceptionRecord,
  type Pricing,
  type Preview,
  type Audit,
  type Raw,
  type JobDetail,
  type PreviewDetail,
} from "./api";

type Tab =
  | "Overview"
  | "Integrations"
  | "Leases & ledger"
  | "Reconciliation"
  | "Billing previews"
  | "Audit & operations";
const navigation = [
  { name: "Overview", icon: LayoutDashboard },
  { name: "Integrations", icon: Layers3 },
  { name: "Leases & ledger", icon: BookOpen },
  { name: "Reconciliation", icon: ShieldCheck },
  { name: "Billing previews", icon: FileCheck2 },
  { name: "Audit & operations", icon: History },
] as const;
const amount = (value: string) =>
  new Intl.NumberFormat("en-ZA", { style: "currency", currency: "ZAR" }).format(
    Number(value),
  );
const date = (value: string | null) =>
  value
    ? new Date(value).toLocaleString("en-ZA", {
        timeZone: "Africa/Johannesburg",
        day: "2-digit",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "No completed import";
const readable = (value: string) => value.replaceAll("_", " ");
const short = (value: string) => value.slice(0, 8);
const currentMonth = () =>
  new Intl.DateTimeFormat("en-CA", {
    timeZone: "Africa/Johannesburg",
    year: "numeric",
    month: "2-digit",
  })
    .format(new Date())
    .replace("/", "-");

export default function App() {
  const [identity, identityState] = useState<Identity | null>(null),
    [initializing, setInitializing] = useState(true);
  const [publicReview, setPublicReview] = useState(false);
  const [sources, setSources] = useState<
    { source_key: string; adapter: string }[]
  >([]);
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]),
    [portfolioId, setPortfolioId] = useState("");
  const [tab, setTab] = useState<Tab>("Overview"),
    [overview, setOverview] = useState<Overview | null>(null);
  const [jobs, setJobs] = useState<Page<Job> | null>(null),
    [leases, setLeases] = useState<Page<Lease> | null>(null),
    [ledger, setLedger] = useState<Page<Ledger> | null>(null),
    [exceptions, setExceptions] = useState<Page<ExceptionRecord> | null>(null),
    [pricing, setPricing] = useState<Pricing[]>([]),
    [previews, setPreviews] = useState<Page<Preview> | null>(null),
    [audits, setAudits] = useState<Page<Audit> | null>(null);
  const [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [loading, setLoading] = useState(false),
    [busy, setBusy] = useState(false),
    [offset, setOffset] = useState(0),
    [search, setSearch] = useState(""),
    [ledgerMode, setLedgerMode] = useState(false),
    [status, setStatus] = useState(""),
    [severity, setSeverity] = useState(""),
    [reason, setReason] = useState("");
  const [month, setMonth] = useState(currentMonth),
    [cutoff, setCutoff] = useState(new Date().toISOString()),
    [modal, setModal] = useState<{ title: string; content: ReactNode } | null>(
      null,
    ),
    [review, setReview] = useState<ExceptionRecord | null>(null),
    [rationale, setRationale] = useState(""),
    [reviewState, setReviewState] = useState("investigating"),
    [jobDetail, setJobDetail] = useState<JobDetail | null>(null),
    [previewDetail, setPreviewDetail] = useState<PreviewDetail | null>(null),
    [detailOffset, setDetailOffset] = useState(0);
  const portfolio = portfolios.find((p) => p.id === portfolioId),
    base = `/api/portfolios/${portfolioId}`,
    readOnly = identity?.read_only ?? identity?.role === "reviewer";
  const saveIdentity = (value: Identity | null) => {
    setIdentity(value);
    identityState(value);
  };
  useEffect(() => {
    api<{ public_review_enabled: boolean }>("/api/auth/options")
      .then((value) => setPublicReview(value.public_review_enabled))
      .catch(() => {});
    api<Identity>("/api/auth/me")
      .then(saveIdentity)
      .catch(() => {})
      .finally(() => setInitializing(false));
  }, []);
  useEffect(() => {
    if (identity)
      api<Portfolio[]>("/api/portfolios")
        .then((rows) => {
          setPortfolios(rows);
          setPortfolioId(rows[0]?.id ?? "");
        })
        .catch((e) => setError(String(e)));
  }, [identity?.email]);
  useEffect(() => {
    setSources([]);
    if (portfolioId)
      api<{ source_key: string; adapter: string }[]>(
        base + "/integration-sources",
      )
        .then(setSources)
        .catch((e) => setError(String(e)));
  }, [portfolioId]);
  const load = useCallback(async () => {
    if (!portfolioId) return;
    setLoading(true);
    try {
      const metrics = await api<Overview>(base + "/overview");
      setOverview(metrics);
      const query = `?offset=${offset}&limit=25`;
      if (tab === "Integrations" || tab === "Audit & operations")
        setJobs(await api<Page<Job>>(base + "/imports" + query));
      if (tab === "Leases & ledger") {
        if (ledgerMode)
          setLedger(await api<Page<Ledger>>(base + "/ledger" + query));
        else
          setLeases(
            await api<Page<Lease>>(
              base + "/leases" + query + `&q=${encodeURIComponent(search)}`,
            ),
          );
      }
      if (tab === "Reconciliation")
        setExceptions(
          await api<Page<ExceptionRecord>>(
            base +
              "/exceptions" +
              query +
              `&status=${status}&severity=${severity}&reason=${reason}&month=${month}`,
          ),
        );
      if (tab === "Billing previews") {
        setPricing(await api<Pricing[]>(base + "/pricing"));
        setPreviews(
          await api<Page<Preview>>(base + "/billing-previews" + query),
        );
      }
      if (tab === "Audit & operations")
        setAudits(await api<Page<Audit>>(base + "/audit" + query));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load records");
    } finally {
      setLoading(false);
    }
  }, [
    portfolioId,
    base,
    tab,
    offset,
    ledgerMode,
    search,
    status,
    severity,
    reason,
    month,
  ]);
  useEffect(() => {
    void load();
  }, [load]);
  useEffect(() => {
    if (!overview?.pending_jobs) return;
    const timer = setInterval(() => void load(), 2500);
    return () => clearInterval(timer);
  }, [overview?.pending_jobs, load]);
  useEffect(() => {
    setOffset(0);
    setJobDetail(null);
    setPreviewDetail(null);
    setModal(null);
    setReview(null);
    setOverview(null);
  }, [portfolioId]);
  const dialogOpen = Boolean(modal || review || jobDetail || previewDetail);
  useEffect(() => {
    if (!dialogOpen) return;
    const previous = document.activeElement as HTMLElement | null;
    const dialog = document.querySelector<HTMLElement>('[role="dialog"]');
    const controls = () =>
      Array.from(
        dialog?.querySelectorAll<HTMLElement>(
          "button:not(:disabled),a[href],input:not(:disabled),select:not(:disabled),textarea:not(:disabled)",
        ) ?? [],
      );
    controls()[0]?.focus();
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setModal(null);
        setReview(null);
        setJobDetail(null);
        setPreviewDetail(null);
      }
      if (event.key === "Tab") {
        const list = controls(),
          first = list[0],
          last = list[list.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
      }
    };
    document.addEventListener("keydown", handler);
    return () => {
      document.removeEventListener("keydown", handler);
      previous?.focus();
    };
  }, [dialogOpen]);
  async function action(work: () => Promise<unknown>, message: string) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await work();
      await load();
      setNotice(message);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }
  function go(next: Tab) {
    setTab(next);
    setOffset(0);
    setError("");
    setNotice("");
    setJobDetail(null);
    setPreviewDetail(null);
  }
  async function signIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await action(
      async () =>
        saveIdentity(
          await post<Identity>("/api/auth/login", {
            email: form.get("email"),
            password: form.get("password"),
          }),
        ),
      "",
    );
  }
  async function inspectJob(job: Job, position = 0) {
    setDetailOffset(position);
    await action(
      async () =>
        setJobDetail(
          await api<JobDetail>(base + `/imports/${job.id}?offset=${position}`),
        ),
      "",
    );
  }
  async function inspectPreview(value: Preview, position = 0) {
    setDetailOffset(position);
    setCutoff(value.cutoff);
    setMonth(value.month);
    await action(
      async () =>
        setPreviewDetail(
          await api<PreviewDetail>(
            base + `/billing-previews/${value.id}?offset=${position}`,
          ),
        ),
      "",
    );
  }
  async function inspectSource(rawId: string) {
    await action(async () => {
      const row = await api<Raw>(base + "/sources/" + rawId);
      setJobDetail(null);
      setPreviewDetail(null);
      setModal({
        title: "Source evidence",
        content: (
          <>
            <dl className="details">
              <dt>External reference</dt>
              <dd>{row.external_id ?? "Invalid record"}</dd>
              <dt>Import batch</dt>
              <dd className="mono">{row.job_id}</dd>
              <dt>Content SHA-256</dt>
              <dd className="mono">{row.content_hash}</dd>
              <dt>Outcome</dt>
              <dd>
                <Badge value={row.status} />
              </dd>
            </dl>
            <pre>{JSON.stringify(row.payload, null, 2)}</pre>
          </>
        ),
      });
    }, "");
  }
  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    data.set("adapter", portfolio?.adapter ?? "");
    await action(
      () =>
        api<Job>(base + "/imports", {
          method: "POST",
          body: data,
          headers: { "Idempotency-Key": crypto.randomUUID() },
        }),
      "Import queued. The worker will publish its row-level report.",
    );
  }
  async function download(value: Preview) {
    await action(async () => {
      const response = await fetch(
        base + `/billing-previews/${value.id}/export.csv`,
        { credentials: "same-origin" },
      );
      if (!response.ok) throw new Error("CSV export failed");
      const url = URL.createObjectURL(await response.blob());
      const link = document.createElement("a");
      link.href = url;
      link.download = `portfolioledger-${value.month}.csv`;
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    }, "CSV downloaded.");
  }
  const jobColumns = [
    {
      label: "Import batch",
      render: (j: Job) => (
        <span className="primary-cell">
          {j.filename}
          <small>
            {short(j.id)} · {date(j.created_at)}
          </small>
        </span>
      ),
    },
    { label: "Status", render: (j: Job) => <Badge value={j.status} /> },
    { label: "Accepted", render: (j: Job) => j.accepted },
    { label: "Duplicates", render: (j: Job) => j.duplicates },
    {
      label: "Quarantined",
      render: (j: Job) => (
        <span className={j.quarantined ? "warning-text" : ""}>
          {j.quarantined}
        </span>
      ),
    },
  ];
  const title: Record<Tab, string> = {
    Overview: "A clear view of your portfolio.",
    Integrations: "Every source, accounted for.",
    "Leases & ledger": "The detail behind the balance.",
    Reconciliation: "Find the difference. Keep the evidence.",
    "Billing previews": "Predictable fees. Transparent calculations.",
    "Audit & operations": "A record of every important action.",
  };
  if (initializing)
    return <div className="loading-screen">Opening PortfolioLedger…</div>;
  if (!identity)
    return (
      <div className="login-layout">
        <div className="login-story">
          <div className="brand">
            <Layers3 /> PortfolioLedger
          </div>
          <div>
            <span className="eyebrow">Synthetic finance operations</span>
            <h1>
              Source to statement.
              <br />
              Every change traceable.
            </h1>
            <p>
              Bring lease data, financial history and monthly administration
              fees into focus.
            </p>
            <div className="story-items">
              <span>
                <ShieldCheck /> Traceable reconciliation
              </span>
              <span>
                <Layers3 /> Repeatable imports
              </span>
              <span>
                <FileCheck2 /> Explainable previews
              </span>
            </div>
          </div>
          <small>
            Independent engineering demonstration · Fictional portfolios only
          </small>
        </div>
        <main className="login-form">
          <span className="eyebrow">Private workspace</span>
          <h2>Welcome back</h2>
          <p>Sign in to your synthetic finance workspace.</p>
          <form onSubmit={signIn}>
            <label>
              Email address
              <input
                name="email"
                type="email"
                autoComplete="username"
                defaultValue="admin@portfolioledger.test"
                required
              />
            </label>
            <label>
              Password
              <input
                name="password"
                type="password"
                autoComplete="current-password"
                required
              />
            </label>
            {error && (
              <div role="alert" className="alert error">
                {error}
              </div>
            )}
            <button className="button dark" disabled={busy}>
              {busy ? "Signing in…" : "Sign in"}
              <ArrowRight size={17} />
            </button>
          </form>
          {publicReview && (
            <button
              className="button subtle"
              onClick={() =>
                action(
                  async () =>
                    saveIdentity(
                      await post<Identity>("/api/auth/public-review", {}),
                    ),
                  "",
                )
              }
              disabled={busy}
            >
              Explore read-only demo <ArrowRight size={17} />
            </button>
          )}
          <div className="login-note">
            <ShieldCheck size={19} />
            <p>
              Use the demo password configured during local setup. No real
              tenant data, invoices or payments.
            </p>
          </div>
        </main>
      </div>
    );
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">
            <Layers3 size={22} />
          </span>
          PortfolioLedger
        </div>
        <div className="workspace-label">Finance workspace</div>
        <nav aria-label="Main navigation">
          {navigation.map(({ name, icon: Icon }) => (
            <button
              key={name}
              aria-label={name}
              className={tab === name ? "active" : ""}
              onClick={() => go(name)}
            >
              <Icon size={18} />
              {name}
              {name === "Reconciliation" && !!overview?.open_exceptions && (
                <span className="nav-count">{overview.open_exceptions}</span>
              )}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="sandbox-card">
            <ShieldCheck size={19} />
            <strong>Synthetic workspace</strong>
            <p>Invented portfolios. Real database operations.</p>
            <span className="tiny-label">No live financial transactions</span>
          </div>
          <button
            className="help-link"
            onClick={() =>
              setModal({
                title: "Your review workspace",
                content: (
                  <>
                    <p>
                      1. Inspect either provider under Integrations. Upload a
                      bundled synthetic fixture or replay an existing batch.
                    </p>
                    <p>
                      2. Trace posted amounts to their source in Leases &
                      ledger.
                    </p>
                    <p>
                      3. Run reconciliation, inspect evidence and review an
                      exception.
                    </p>
                    <p>
                      4. Generate a monthly administration-fee preview and
                      download its CSV. Keep the same cutoff to reproduce a
                      result.
                    </p>
                    <p>
                      All activity is persisted in PostgreSQL. This project is
                      independent and has no affiliation with any real
                      property-management or insurance provider.
                    </p>
                  </>
                ),
              })
            }
          >
            <CircleHelp size={17} /> Reviewer guide
          </button>
          <div className="user">
            <div className="avatar">{identity.role[0].toUpperCase()}</div>
            <div>
              <strong>
                {identity.role === "admin"
                  ? "Demo administrator"
                  : readable(identity.role)}
              </strong>
              <small>{identity.email}</small>
            </div>
            <button
              className="icon-button"
              aria-label="Sign out"
              onClick={() =>
                action(async () => {
                  await post("/api/auth/logout");
                  saveIdentity(null);
                  setPortfolioId("");
                }, "")
              }
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <span>/</span> <strong>{tab}</strong>
          </div>
          <div className="top-right">
            <button
              className="icon-button mobile-logout"
              aria-label="Sign out"
              onClick={() =>
                action(async () => {
                  await post("/api/auth/logout");
                  saveIdentity(null);
                  setPortfolios([]);
                  setPortfolioId("");
                }, "")
              }
            >
              <LogOut size={18} />
            </button>
            <span className="environment">
              <span /> {readOnly ? "Read-only demo" : "Private demo"}
            </span>
            <span className="top-avatar">PL</span>
          </div>
        </header>
        <main className="main">
          <div className="context-row">
            <label className="portfolio-select">
              <Building2 size={17} />
              <select
                aria-label="Select portfolio"
                value={portfolioId}
                onChange={(e) => setPortfolioId(e.target.value)}
              >
                {portfolios.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </label>
            <button
              className="button subtle"
              onClick={() => {
                setError("");
                void load();
              }}
              disabled={loading}
            >
              <RefreshCw size={15} className={loading ? "spinning" : ""} />
              Refresh
            </button>
          </div>
          <div className="page-title">
            <div>
              <span className="eyebrow">
                {tab === "Overview" ? "Portfolio overview" : tab}
              </span>
              <h1>{title[tab]}</h1>
              <p>
                {tab === "Overview"
                  ? "Source health, financial activity and the work that needs your attention."
                  : `${portfolio?.name ?? "Workspace"} · All amounts in ZAR · Display times SAST`}
              </p>
            </div>
            {tab === "Overview" && (
              <button
                className="button dark"
                onClick={() => go("Integrations")}
              >
                <Upload size={16} />
                {readOnly ? "View integrations" : "Import data"}
              </button>
            )}
          </div>
          {error && (
            <div className="alert error" role="alert">
              <span>{error}</span>
              <button aria-label="Dismiss error" onClick={() => setError("")}>
                <X size={16} />
              </button>
            </div>
          )}
          {notice && (
            <div className="alert success" role="status">
              <Check size={16} />
              {notice}
            </div>
          )}
          {loading && !overview && (
            <div className="loading-bar" aria-label="Loading workspace" />
          )}
          {tab === "Overview" && overview && (
            <>
              <div className="metrics">
                <div>
                  <span>
                    Active leases
                    <Building2 size={16} />
                  </span>
                  <strong>{overview.active_leases}</strong>
                  <small>{overview.leases} normalized leases</small>
                </div>
                <div>
                  <span>
                    Rental ledger balance
                    <BookOpen size={16} />
                  </span>
                  <strong>{amount(overview.balance)}</strong>
                  <small>Signed receivable · all posted entries</small>
                </div>
                <div>
                  <span>
                    Open exceptions
                    <ShieldCheck size={16} />
                  </span>
                  <strong>
                    {overview.open_exceptions}
                    <span className="metric-note">to review</span>
                  </strong>
                  <small>Open and investigating</small>
                </div>
                <div>
                  <span>
                    Latest fee preview
                    <FileCheck2 size={16} />
                  </span>
                  <strong>
                    {overview.latest_preview
                      ? amount(overview.latest_preview.total)
                      : "—"}
                  </strong>
                  <small>
                    {overview.latest_preview
                      ? `${overview.latest_preview.month} · administration fees`
                      : "Generate your first monthly preview"}
                  </small>
                </div>
              </div>
              <div className="overview-split">
                <Panel
                  title="Integration health"
                  subtitle="Know where your data stands."
                  action={
                    <button
                      className="text-button"
                      onClick={() => go("Integrations")}
                    >
                      View integration <ArrowRight size={14} />
                    </button>
                  }
                >
                  <div className="integration-summary">
                    <div className="provider-logo">
                      {portfolio?.adapter === "atlaspm" ? "A" : "M"}
                    </div>
                    <div>
                      <h3>
                        {portfolio?.adapter === "atlaspm"
                          ? "AtlasPM"
                          : "MeridianRent"}
                      </h3>
                      <p>
                        {portfolio?.adapter === "atlaspm"
                          ? "CSV snapshot feed"
                          : "JSON incremental feed"}{" "}
                        · Synthetic provider
                      </p>
                    </div>
                    <Badge value={overview.source_stale ? "stale" : "ready"} />
                  </div>
                  <div className="health-grid">
                    <div>
                      <span>LAST COMPLETED SYNC</span>
                      <strong>{date(overview.last_sync)}</strong>
                    </div>
                    <div>
                      <span>ACCEPTED SOURCE ROWS</span>
                      <strong>
                        {overview.processed_rows.toLocaleString("en-ZA")}
                      </strong>
                    </div>
                    <div>
                      <span>QUARANTINED ROWS</span>
                      <strong>{overview.quarantined_rows}</strong>
                    </div>
                    <div>
                      <span>QUEUED / PROCESSING</span>
                      <strong>{overview.pending_jobs}</strong>
                    </div>
                  </div>
                </Panel>
                <section className="next-step">
                  <div className="step-icon">
                    <ShieldCheck size={22} />
                  </div>
                  <span className="eyebrow">Next action</span>
                  <h2>
                    {overview.open_exceptions
                      ? "Bring exceptions into focus."
                      : "Check your source against the ledger."}
                  </h2>
                  <p>
                    Compare monthly rent charges with normalized lease terms.
                    Every discrepancy keeps its source evidence.
                  </p>
                  <button
                    className="button light"
                    onClick={() => go("Reconciliation")}
                  >
                    Open reconciliation
                    <ArrowRight size={16} />
                  </button>
                </section>
              </div>
              <Panel
                title="Recent imports"
                subtitle="Persisted outcomes, including duplicates and rejected records."
                action={
                  <button
                    className="text-button"
                    onClick={() => go("Integrations")}
                  >
                    All imports <ArrowRight size={14} />
                  </button>
                }
              >
                <Table
                  rows={overview.recent_jobs}
                  columns={jobColumns}
                  onClick={inspectJob}
                />
              </Panel>
              <div className="footnote">
                <ShieldCheck size={15} />
                <span>
                  Rental ledger activity and administration-fee previews are
                  calculated separately. No invoices or payments are initiated.
                </span>
              </div>
            </>
          )}
          {tab === "Integrations" && (
            <>
              <div className="provider-grid">
                {[
                  {
                    key: "atlaspm",
                    name: "AtlasPM",
                    type: "CSV / SNAPSHOT",
                    description:
                      "Lease occupancy and signed ledger rows in a tabular snapshot.",
                    fields:
                      "record_id → external ID · lease_ref → lease · amount_zar → signed amount",
                    file: "atlaspm/snapshot.csv",
                  },
                  {
                    key: "meridianrent",
                    name: "MeridianRent",
                    type: "JSON / INCREMENTAL",
                    description:
                      "Contract and financial events with explicit provider revisions.",
                    fields:
                      "eventId → external ID · contractId → lease · value → signed amount",
                    file: "meridianrent/events.json",
                  },
                ].map((p) => (
                  <section
                    className={`provider-card ${portfolio?.adapter === p.key ? "selected" : ""}`}
                    key={p.key}
                  >
                    <div className="provider-top">
                      <span className="provider-logo">{p.name[0]}</span>
                      <span className="tiny-label">{p.type}</span>
                    </div>
                    <h2>{p.name}</h2>
                    <p>{p.description}</p>
                    <div className="mapping">{p.fields}</div>
                    <div className="provider-footer">
                      <span>
                        {portfolio?.adapter === p.key
                          ? "Configured for this portfolio"
                          : "Inspect example format"}
                      </span>
                      <a
                        href={"/fixtures/" + p.file}
                        download
                        className="text-button"
                      >
                        <ArrowDownToLine size={15} />
                        Example
                      </a>
                    </div>
                  </section>
                ))}
              </div>
              <Panel
                title="Import a source file"
                subtitle="Up to 8 MiB / 20,000 rows. Invalid rows are quarantined with reasons."
              >
                <form className="upload-form" onSubmit={upload}>
                  <label className="file-label">
                    <Upload size={21} />
                    <span>
                      Select{" "}
                      {portfolio?.adapter === "atlaspm"
                        ? "CSV snapshot"
                        : "JSON event feed"}
                    </span>
                    <input
                      aria-label="Source file"
                      type="file"
                      name="file"
                      accept={
                        portfolio?.adapter === "atlaspm" ? ".csv" : ".json"
                      }
                      required
                      disabled={readOnly}
                    />
                  </label>
                  <label>
                    Configured integration source
                    <select
                      name="source_key"
                      key={portfolioId}
                      required
                      disabled={readOnly || !sources.length}
                    >
                      {sources.map((source) => (
                        <option
                          key={source.source_key}
                          value={source.source_key}
                        >
                          {source.source_key}
                        </option>
                      ))}
                    </select>
                  </label>
                  <button
                    className="button dark"
                    disabled={busy || readOnly || !sources.length}
                  >
                    <Upload size={15} />
                    Queue import
                  </button>
                </form>
                <p className="inline-note">
                  Only registered integration sources can publish records.
                  Replays retain the original source identity and financial
                  lineage.
                </p>
              </Panel>
              <Panel
                title="Import history"
                subtitle="Select a batch for validation outcomes and retry diagnostics."
              >
                {jobs && (
                  <>
                    <Table
                      rows={jobs.items}
                      columns={jobColumns}
                      onClick={inspectJob}
                    />
                    <Pager
                      offset={offset}
                      total={jobs.total}
                      onChange={setOffset}
                    />
                  </>
                )}
              </Panel>
            </>
          )}
          {tab === "Leases & ledger" && (
            <Panel
              title="Normalized records"
              subtitle="Every financial posting retains its provider revision and source lineage."
              action={
                <div className="segmented">
                  <button
                    className={!ledgerMode ? "selected" : ""}
                    onClick={() => {
                      setLedgerMode(false);
                      setOffset(0);
                    }}
                  >
                    Leases
                  </button>
                  <button
                    className={ledgerMode ? "selected" : ""}
                    onClick={() => {
                      setLedgerMode(true);
                      setOffset(0);
                    }}
                  >
                    Ledger
                  </button>
                </div>
              }
            >
              {!ledgerMode && (
                <label className="search">
                  <Search size={16} />
                  <input
                    placeholder="Search lease reference"
                    aria-label="Search leases"
                    value={search}
                    onChange={(e) => {
                      setSearch(e.target.value);
                      setOffset(0);
                    }}
                  />
                </label>
              )}
              {ledgerMode
                ? ledger && (
                    <>
                      <Table
                        rows={ledger.items}
                        onClick={(row) => inspectSource(row.raw_id)}
                        columns={[
                          {
                            label: "Source event",
                            render: (row) => (
                              <span className="primary-cell mono">
                                {row.external_id}
                                <small>
                                  {row.source_key} · revision {row.revision}
                                </small>
                              </span>
                            ),
                          },
                          {
                            label: "Type",
                            render: (row) => <Badge value={row.kind} />,
                          },
                          {
                            label: "Effective date",
                            render: (row) => row.effective_date,
                          },
                          {
                            label: "Amount",
                            render: (row) => (
                              <span className="money">
                                {amount(row.amount)}
                              </span>
                            ),
                          },
                          {
                            label: "Correction lineage",
                            render: (row) => (
                              <span className="mono muted">
                                {row.reverses_id
                                  ? `Reverses ${short(row.reverses_id)}`
                                  : row.reason}
                              </span>
                            ),
                          },
                        ]}
                      />
                      <Pager
                        offset={offset}
                        total={ledger.total}
                        onChange={setOffset}
                      />
                    </>
                  )
                : leases && (
                    <>
                      <Table
                        rows={leases.items}
                        onClick={(row) => inspectSource(row.raw_id)}
                        columns={[
                          {
                            label: "Lease reference",
                            render: (row) => (
                              <span className="primary-cell">
                                {row.external_id}
                                <small>
                                  {row.source_key} · revision {row.revision}
                                </small>
                              </span>
                            ),
                          },
                          {
                            label: "Status",
                            render: (row) => <Badge value={row.status} />,
                          },
                          {
                            label: "Monthly rent",
                            render: (row) => amount(row.rent),
                          },
                          {
                            label: "Start date",
                            render: (row) => row.start_date,
                          },
                          {
                            label: "End date",
                            render: (row) => row.end_date ?? "Open-ended",
                          },
                        ]}
                      />
                      <Pager
                        offset={offset}
                        total={leases.total}
                        onChange={setOffset}
                      />
                    </>
                  )}
            </Panel>
          )}
          {(tab === "Reconciliation" || tab === "Billing previews") && (
            <div className="run-controls">
              <label>
                Calendar month
                <input
                  type="month"
                  value={month}
                  onChange={(e) => {
                    setMonth(e.target.value);
                    setOffset(0);
                  }}
                  required
                />
              </label>
              <label className="cutoff">
                Source cutoff (UTC)
                <input
                  aria-label="Source cutoff UTC"
                  value={cutoff}
                  onChange={(e) => setCutoff(e.target.value)}
                />
              </label>
              <button
                className="button subtle"
                onClick={() => setCutoff(new Date().toISOString())}
              >
                Use current cutoff
              </button>
              <button
                className="button dark"
                disabled={busy || readOnly || !month}
                onClick={() =>
                  action(
                    async () => {
                      if (tab === "Reconciliation")
                        await post(base + "/reconciliations", {
                          month,
                          cutoff,
                        });
                      else {
                        const result = await post<Preview>(
                          base + "/billing-previews",
                          { month, cutoff },
                        );
                        setPreviewDetail(
                          await api<PreviewDetail>(
                            base + `/billing-previews/${result.id}`,
                          ),
                        );
                        setDetailOffset(0);
                      }
                    },
                    tab === "Reconciliation"
                      ? "Reconciliation saved with source evidence."
                      : "Immutable fee preview ready. Repeating this cutoff returns the same preview.",
                  )
                }
              >
                <RefreshCw size={15} />
                {tab === "Reconciliation"
                  ? "Run reconciliation"
                  : "Calculate preview"}
              </button>
            </div>
          )}
          {tab === "Reconciliation" && (
            <Panel
              title="Exceptions to review"
              subtitle="Resolution records your rationale. It never changes a ledger balance."
            >
              <div className="filters">
                <SlidersHorizontal size={16} />
                <select
                  aria-label="Filter exception status"
                  value={status}
                  onChange={(e) => {
                    setStatus(e.target.value);
                    setOffset(0);
                  }}
                >
                  <option value="">All statuses</option>
                  {["open", "investigating", "resolved", "dismissed"].map(
                    (v) => (
                      <option key={v} value={v}>
                        {readable(v)}
                      </option>
                    ),
                  )}
                </select>
                <select
                  aria-label="Filter severity"
                  value={severity}
                  onChange={(e) => {
                    setSeverity(e.target.value);
                    setOffset(0);
                  }}
                >
                  <option value="">All severities</option>
                  <option>high</option>
                  <option>medium</option>
                </select>
                <select
                  aria-label="Filter reason"
                  value={reason}
                  onChange={(e) => {
                    setReason(e.target.value);
                    setOffset(0);
                  }}
                >
                  <option value="">All reasons</option>
                  {[
                    "missing_charge",
                    "charge_mismatch",
                    "source_quarantine",
                    "unallocated_credit",
                  ].map((v) => (
                    <option key={v} value={v}>
                      {readable(v)}
                    </option>
                  ))}
                </select>
              </div>
              {exceptions && (
                <>
                  <Table
                    rows={exceptions.items}
                    onClick={(row) => {
                      setReview(row);
                      setRationale("");
                      setReviewState("investigating");
                    }}
                    columns={[
                      {
                        label: "Exception",
                        render: (row) => (
                          <span className="primary-cell">
                            {readable(row.reason)}
                            <small>
                              Run {short(row.run_id)} · {date(row.created_at)}
                            </small>
                          </span>
                        ),
                      },
                      {
                        label: "Severity",
                        render: (row) => <Badge value={row.severity} />,
                      },
                      {
                        label: "Status",
                        render: (row) => <Badge value={row.status} />,
                      },
                      {
                        label: "Evidence",
                        render: (row) => (
                          <span className="muted">
                            {Object.keys(row.evidence).length} evidence fields
                          </span>
                        ),
                      },
                    ]}
                  />
                  <Pager
                    offset={offset}
                    total={exceptions.total}
                    onChange={setOffset}
                  />
                </>
              )}
            </Panel>
          )}
          {tab === "Billing previews" && (
            <>
              <div className="pricing-note">
                <FileCheck2 size={22} />
                <div>
                  <strong>
                    Administration fee ·{" "}
                    {pricing[0]
                      ? amount(pricing[0].monthly_fee)
                      : "No pricing configured"}{" "}
                    per eligible lease / month
                  </strong>
                  <p>
                    Active on the first day of the month, inclusive lease end
                    date. No proration. ZAR, two decimals, half-up rounding.
                    Pricing version {pricing[0]?.version ?? "—"}. Preview only.
                  </p>
                </div>
              </div>
              <Panel
                title="Saved previews"
                subtitle="A portfolio, month, cutoff and pricing version identifies one immutable result."
              >
                {previews && (
                  <>
                    <Table
                      rows={previews.items}
                      onClick={inspectPreview}
                      columns={[
                        {
                          label: "Month",
                          render: (row) => (
                            <span className="primary-cell">
                              {row.month}
                              <small>Preview {short(row.id)}</small>
                            </span>
                          ),
                        },
                        {
                          label: "Source cutoff",
                          render: (row) => date(row.cutoff),
                        },
                        {
                          label: "Pricing version",
                          render: (row) => `v${row.config.version}`,
                        },
                        {
                          label: "Total",
                          render: (row) => <strong>{amount(row.total)}</strong>,
                        },
                        {
                          label: "Exception snapshot",
                          render: (row) =>
                            `${row.unresolved_exceptions.length} unresolved`,
                        },
                        {
                          label: "Export",
                          render: (row) => (
                            <button
                              className="button subtle small"
                              disabled={busy}
                              onClick={() => download(row)}
                            >
                              <ArrowDownToLine size={14} />
                              CSV
                            </button>
                          ),
                        },
                      ]}
                    />
                    <Pager
                      offset={offset}
                      total={previews.total}
                      onChange={setOffset}
                    />
                  </>
                )}
              </Panel>
            </>
          )}
          {tab === "Audit & operations" && (
            <>
              <div className="operations-stats">
                <Activity size={20} />
                <strong>Persisted operational state</strong>
                <span>{overview?.pending_jobs ?? 0} pending jobs</span>
                <span>{overview?.failed_jobs ?? 0} failed jobs</span>
                <span>{overview?.quarantined_rows ?? 0} quarantined rows</span>
                <button
                  className="text-button"
                  onClick={() =>
                    action(async () => {
                      const health = await api<{
                        status: string;
                        schema: string;
                      }>("/ready");
                      setModal({
                        title: "Readiness check",
                        content: (
                          <p>
                            Database {health.status}. Applied schema:{" "}
                            {health.schema}. Checked at{" "}
                            {date(new Date().toISOString())}.
                          </p>
                        ),
                      });
                    }, "")
                  }
                >
                  Check readiness
                </button>
              </div>
              <Panel
                title="Execution & audit timeline"
                subtitle="Server-assigned actors, correlation references and state changes."
              >
                {audits && (
                  <>
                    <Table
                      rows={audits.items}
                      onClick={(row) =>
                        setModal({
                          title: readable(row.action),
                          content: (
                            <>
                              <dl className="details">
                                <dt>Actor</dt>
                                <dd className="mono">{row.actor_id}</dd>
                                <dt>Resource</dt>
                                <dd className="mono">{row.resource_id}</dd>
                                <dt>Correlation ID</dt>
                                <dd className="mono">{row.correlation_id}</dd>
                              </dl>
                              <pre>{JSON.stringify(row.details, null, 2)}</pre>
                            </>
                          ),
                        })
                      }
                      columns={[
                        {
                          label: "Action",
                          render: (row) => (
                            <span className="primary-cell">
                              {row.action}
                              <small>{date(row.created_at)}</small>
                            </span>
                          ),
                        },
                        {
                          label: "Resource",
                          render: (row) => (
                            <span className="mono">
                              {short(row.resource_id)}
                            </span>
                          ),
                        },
                        {
                          label: "Actor",
                          render: (row) => (
                            <span className="mono">{short(row.actor_id)}</span>
                          ),
                        },
                        {
                          label: "Correlation",
                          render: (row) => (
                            <span className="mono muted">
                              {short(row.correlation_id)}
                            </span>
                          ),
                        },
                      ]}
                    />
                    <Pager
                      offset={offset}
                      total={audits.total}
                      onChange={setOffset}
                    />
                  </>
                )}
              </Panel>
              <Panel
                title="Worker diagnostics"
                subtitle="Claims, bounded attempts and durable outcomes."
              >
                {jobs && (
                  <Table
                    rows={jobs.items}
                    onClick={inspectJob}
                    columns={[
                      {
                        label: "Import",
                        render: (j) => (
                          <span className="primary-cell">
                            {j.filename}
                            <small>{short(j.id)}</small>
                          </span>
                        ),
                      },
                      {
                        label: "Status",
                        render: (j) => <Badge value={j.status} />,
                      },
                      { label: "Attempts", render: (j) => `${j.attempts} / 3` },
                      {
                        label: "Error summary",
                        render: (j) => j.error ?? "No processing error",
                      },
                    ]}
                  />
                )}
              </Panel>
            </>
          )}
          <footer>
            <span>
              PortfolioLedger <span className="muted">/</span> Finance
              operations
            </span>
            <span>Independent synthetic-data demonstration</span>
          </footer>
        </main>
      </div>
      {(modal || review || jobDetail || previewDetail) && (
        <div
          className="modal-backdrop"
          onClick={() => {
            if (!busy) {
              setModal(null);
              setReview(null);
              setJobDetail(null);
              setPreviewDetail(null);
            }
          }}
        >
          <section
            role="dialog"
            aria-modal="true"
            aria-label={
              modal?.title ??
              (review
                ? "Review exception"
                : jobDetail
                  ? "Import report"
                  : "Preview breakdown")
            }
            className="modal"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header">
              <h2>
                {modal?.title ??
                  (review
                    ? "Review exception"
                    : jobDetail
                      ? "Import report"
                      : "Preview breakdown")}
              </h2>
              <button
                className="icon-button"
                aria-label="Close dialog"
                onClick={() => {
                  setModal(null);
                  setReview(null);
                  setJobDetail(null);
                  setPreviewDetail(null);
                }}
              >
                <X size={20} />
              </button>
            </div>
            {modal?.content}
            {review && (
              <>
                <div className="review-heading">
                  <Badge value={review.severity} />
                  <Badge value={review.status} />
                  <h3>{readable(review.reason)}</h3>
                </div>
                <pre>{JSON.stringify(review.evidence, null, 2)}</pre>
                {!readOnly &&
                  !["resolved", "dismissed"].includes(review.status) && (
                    <form
                      className="review-form"
                      onSubmit={(e) => {
                        e.preventDefault();
                        void action(async () => {
                          await post(
                            base + `/exceptions/${review.id}/resolve`,
                            {
                              status: reviewState,
                              rationale,
                            },
                          );
                          setReview(null);
                        }, "Review recorded in the audit trail.");
                      }}
                    >
                      <label>
                        Next status
                        <select
                          value={reviewState}
                          onChange={(e) => setReviewState(e.target.value)}
                        >
                          <option value="investigating">Investigating</option>
                          <option value="resolved">Resolved</option>
                          <option value="dismissed">Dismissed</option>
                        </select>
                      </label>
                      <label>
                        Review rationale
                        <textarea
                          value={rationale}
                          onChange={(e) => setRationale(e.target.value)}
                          minLength={5}
                          maxLength={1000}
                          required
                          placeholder="Explain what the source evidence shows…"
                        />
                      </label>
                      <button
                        className="button dark"
                        disabled={busy || readOnly}
                      >
                        Save review
                        <Check size={15} />
                      </button>
                    </form>
                  )}
              </>
            )}
            {jobDetail && (
              <>
                <div className="report-summary">
                  <Badge value={jobDetail.job.status} />
                  <span>{jobDetail.job.accepted} accepted</span>
                  <span>{jobDetail.job.duplicates} duplicate</span>
                  <span>{jobDetail.job.quarantined} quarantined</span>
                </div>
                <dl className="details">
                  <dt>Batch</dt>
                  <dd className="mono">{jobDetail.job.id}</dd>
                  <dt>Checksum</dt>
                  <dd className="mono">{jobDetail.job.checksum}</dd>
                  <dt>Attempts / error</dt>
                  <dd>
                    {jobDetail.job.attempts} /{" "}
                    {jobDetail.job.error ?? "No processing error"}
                  </dd>
                </dl>
                <Table
                  rows={jobDetail.rows}
                  onClick={(row) => inspectSource(row.id)}
                  columns={[
                    {
                      label: "Source row",
                      render: (row) => (
                        <span className="primary-cell">
                          {row.external_id ?? `Row ${row.row_number}`}
                          <small>Row {row.row_number}</small>
                        </span>
                      ),
                    },
                    {
                      label: "Outcome",
                      render: (row) => <Badge value={row.status} />,
                    },
                    {
                      label: "Reason",
                      render: (row) => row.reason ?? "Validated",
                    },
                  ]}
                />
                <Pager
                  offset={detailOffset}
                  total={
                    jobDetail.job.accepted +
                    jobDetail.job.duplicates +
                    jobDetail.job.quarantined
                  }
                  onChange={(n) => void inspectJob(jobDetail.job, n)}
                />
                {!readOnly && (
                  <button
                    className="button dark"
                    disabled={busy || readOnly}
                    onClick={() =>
                      action(async () => {
                        await api<Job>(
                          base + `/imports/${jobDetail.job.id}/replay`,
                          {
                            method: "POST",
                            headers: { "Idempotency-Key": crypto.randomUUID() },
                          },
                        );
                        setJobDetail(null);
                      }, "Replay queued. Existing financial events will be deduplicated.")
                    }
                  >
                    <RefreshCw size={15} />
                    Replay this import
                  </button>
                )}
              </>
            )}
            {previewDetail && (
              <>
                <div className="preview-total">
                  <span>
                    {previewDetail.preview.month} · Administration-fee preview
                  </span>
                  <strong>{amount(previewDetail.preview.total)}</strong>
                  <small>
                    v{previewDetail.preview.config.version} ·{" "}
                    {previewDetail.preview.unresolved_exceptions.length}{" "}
                    unresolved exceptions at cutoff
                  </small>
                </div>
                <Table
                  rows={previewDetail.lines}
                  columns={[
                    { label: "Lease", render: (row) => row.external_id },
                    {
                      label: "Eligibility",
                      render: (row) => (
                        <Badge value={row.eligible ? "eligible" : "excluded"} />
                      ),
                    },
                    {
                      label: "Rule outcome",
                      render: (row) => readable(row.reason),
                    },
                    { label: "Amount", render: (row) => amount(row.amount) },
                  ]}
                />
                <Pager
                  offset={detailOffset}
                  total={previewDetail.total}
                  onChange={(n) =>
                    void inspectPreview(previewDetail.preview, n)
                  }
                />
                <button
                  className="button dark"
                  disabled={busy}
                  onClick={() => download(previewDetail.preview)}
                >
                  <ArrowDownToLine size={15} />
                  Download CSV
                </button>
              </>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
