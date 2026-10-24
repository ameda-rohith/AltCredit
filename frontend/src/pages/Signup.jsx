import { createContext, useContext, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../auth'
import { Brand } from '../components/Layout'
import { ThemeToggle } from '../components/ThemeToggle'
import { CountUp, Icon, ScoreRing, fmt, tierMeta } from '../components/ui'
import './signup.css'

const STEPS = ['Account', 'About you', 'Work & home', 'Money habits']
const EDU = ['High School', 'Diploma', "Bachelor's", "Master's", 'PhD', 'Below high school']
const EMP = ['Employed', 'Self-Employed', 'Student', 'Unemployed']
const TIERS = [['1', 'Tier 1 (metro)'], ['2', 'Tier 2 (large city)'], ['3', 'Tier 3 (town / rural)']]
const VOLATILITY = [['0.04', 'Very steady (≤ 5% swing)'], ['0.08', 'Some variation (5–10%)'], ['0.15', 'Noticeable (10–20%)'], ['0.25', 'Large swings (> 20%)']]
const LATE = [['none', 'No missed payments'], ['30', 'Up to 30–59 days late'], ['60', 'Up to 60–89 days late'], ['90', '90+ days late']]

// Plain-language answers. Values are the underlying % / day / count figures the scorer expects.
const ALWAYS = [['100', 'Always'], ['90', 'Almost always'], ['75', 'Most of the time'], ['50', 'About half the time'], ['25', 'Rarely']]
const ESSENTIAL = [['90', 'Almost all of it'], ['75', 'Most of it'], ['55', 'About half'], ['35', 'Less than half'], ['20', 'Only a small part']]
const EMI = [['0', 'None'], ['10', 'A little (under 15% of income)'], ['25', 'Some (15–35%)'], ['45', 'A lot (35–50%)'], ['60', 'More than half']]
const CARD_USE = [['10', 'Very little (under 30% of the limit)'], ['45', 'About half'], ['75', 'Most of it'], ['95', 'Nearly maxed out']]
const SAVINGS = [['0', 'No savings'], ['7', 'About a week'], ['30', 'About a month'], ['90', 'About 3 months'], ['180', '6 months or more']]
const HABITS = [['0', 'None of these'], ['1', 'One of these'], ['2', 'Two of these'], ['3', 'All three']]
const FLAGS = [['0', 'None'], ['1', 'One'], ['2', 'Two'], ['3', 'Three'], ['4', 'Four or more']]
const DONT_KNOW = "I don't know / skip"

const INITIAL = {
  full_name: '', email: '', password: '', confirm: '',
  age: '', city_tier: '1', education_level: "Bachelor's", employment_status: 'Employed', monthly_income: '',
  months_at_job: '', housing: 'rent', rent_on_time_months: '', digital_pct: '',
  monthly_spend: '', essential_pct: '', savings_days: '', on_time_pct: '', volatility: '', dti_pct: '', util_pct: '',
  late: '', positive_habits: '', risk_flags: '', share_with_lenders: false,
}

const num = (v) => (v === '' ? undefined : Number(v))
const pct = (v) => (v === '' ? undefined : Number(v) / 100)

function buildPayload(f) {
  const late = f.late
  const payload = {
    full_name: f.full_name.trim(), email: f.email.trim(), password: f.password,
    age: num(f.age), city_tier: num(f.city_tier), education_level: f.education_level, employment_status: f.employment_status,
    monthly_income: num(f.monthly_income), months_at_job: num(f.months_at_job), housing: f.housing,
    rent_on_time_months: f.housing === 'rent' ? num(f.rent_on_time_months) : undefined,
    digital_payment_rate: pct(f.digital_pct), monthly_spend: num(f.monthly_spend), essential_pct: pct(f.essential_pct),
    savings_days: num(f.savings_days), on_time_rate: pct(f.on_time_pct), cashflow_volatility: num(f.volatility),
    dti: pct(f.dti_pct), credit_util: pct(f.util_pct), positive_habits: num(f.positive_habits), risk_flags: num(f.risk_flags),
    share_with_lenders: f.share_with_lenders,
  }
  if (late) {
    payload.delinq_30plus = late === 'none' ? 0 : 1
    payload.delinq_60plus = late === '60' || late === '90' ? 1 : 0
    payload.delinq_90plus = late === '90' ? 1 : 0
  }
  return Object.fromEntries(Object.entries(payload).filter(([, v]) => v !== undefined))
}

// Defined at module level (not inside Signup) so inputs keep focus while typing.
const FormCtx = createContext(null)

// Required fields stop being required once a bank statement is attached; optional numeric
// fields get an "I don't know" tick that clears the value (it is then scored as missing).
function Field({ k, label, hint, req, core, unit, ...p }) {
  const { f, set, file, dk, toggleDk } = useContext(FormCtx)
  const required = req && (!file || core)
  const input = <input value={f[k]} onChange={set(k)} required={required} disabled={!!dk[k]} {...p} />
  return (
    <div className="field">
      <label className="field"><span>{label}{required && <b className="req">*</b>}{hint && <small>{hint}</small>}</span>
        {unit ? <div className="unit" data-unit={unit}>{input}</div> : input}</label>
      {!required && <label className="dk"><input type="checkbox" checked={!!dk[k]} onChange={(e) => toggleDk(k, e.target.checked)} /> I don’t know</label>}
    </div>
  )
}

function Select({ k, label, hint, options, req }) {
  const { f, set, file } = useContext(FormCtx)
  const required = req && !file
  return (
    <label className="field"><span>{label}{required && <b className="req">*</b>}{hint && <small>{hint}</small>}</span>
      <select value={f[k]} onChange={set(k)} required={required}>{!required && <option value="">{DONT_KNOW}</option>}{options.map((o) => (Array.isArray(o) ? <option key={o[0]} value={o[0]}>{o[1]}</option> : <option key={o}>{o}</option>))}</select></label>
  )
}

export default function Signup() {
  const { register } = useAuth()
  const nav = useNavigate()
  const [step, setStep] = useState(0)
  const [f, setF] = useState(INITIAL)
  const [file, setFile] = useState(null)
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState(null)
  const [dk, setDk] = useState({})
  const fileInput = useRef()
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })
  const toggleDk = (k, on) => { setDk({ ...dk, [k]: on }); if (on) setF({ ...f, [k]: '' }) }

  const next = (e) => {
    e.preventDefault()
    setErr('')
    if (step === 0 && f.password !== f.confirm) return setErr('Passwords do not match.')
    if (step < STEPS.length - 1) return setStep(step + 1)
    submit()
  }

  const submit = async () => {
    setBusy(true); setErr('')
    try {
      const res = await register(buildPayload(f))
      let final = { ...res, upload: null }
      if (file) {
        try {
          const up = await api.uploadTransactions(res.user_id, file)
          final = { ...final, credit_score: up.credit_score, risk_tier: up.risk_tier, missing_fields: up.missing_fields, upload: { ok: true, n: up.transactions_read } }
        } catch (ex) { final.upload = { ok: false, msg: ex.message } }
      }
      setResult(final)
    } catch (ex) {
      setErr(ex.message)
      if (/email/i.test(ex.message) && !/email:/.test(ex.message)) setStep(0)
    } finally { setBusy(false) }
  }

  const uploadBox = (compact) => file ? (
    <div className="su-attach ok" role="status"><Icon name="task_alt" /><div><strong>{file.name} attached</strong><small>We’ll read your score from the statement. Every question below is now optional.</small></div>
      <button type="button" className="btn btn-ghost btn-sm" onClick={() => setFile(null)}>Remove</button></div>
  ) : (
    <div className={`drop ${compact ? 'su-attach' : ''}`} style={{ padding: 18 }}>
      <Icon name="upload_file" /><strong>{compact ? 'Have a bank statement? Upload it and skip the questions' : 'Optional: upload a bank statement (CSV)'}</strong>
      <small>Columns: date, amount, category, type, status</small>
      <button type="button" className="btn btn-tint btn-sm" onClick={() => fileInput.current.click()}>Browse</button>
    </div>
  )

  if (result) {
    const t = tierMeta(result.risk_tier)
    return (
      <div className="signup">
      <ThemeToggle className="theme-fab" />
        <Brand />
        <div className="su-card su-done">
          <h1>You’re in, and scored!</h1>
          <ScoreRing value={result.credit_score} colour={t.colour} size={128}><Icon name="verified" /></ScoreRing>
          <div className="score-num"><CountUp value={result.credit_score} /><small className="muted">/ 1000</small></div>
          <span className={`chip ${t.chip}`}>{result.risk_tier}</span>
          <p className="su-hint">Your user ID is <b>{result.user_id}</b>. Your profile is saved and you can sign in with it or your email.</p>
          {result.upload?.ok && <div className="su-note"><Icon name="check_circle" />Statement parsed: {result.upload.n} transactions added to your score.</div>}
          {result.upload && !result.upload.ok && <div className="err">Your statement couldn’t be read ({result.upload.msg}). You can retry from the dashboard.</div>}
          {result.missing_fields.length > 0 && <div className="su-note"><Icon name="info" />{result.missing_fields.length} input(s) were left blank and scored conservatively. Add them or upload a statement from your dashboard to raise your score.</div>}
          <button className="btn btn-primary btn-lg" onClick={() => nav('/dashboard')}>Go to my dashboard <Icon name="arrow_forward" /></button>
        </div>
      </div>
    )
  }

  return (
    <div className="signup">
      <ThemeToggle className="theme-fab" />
      <Link to="/" aria-label="ALTcredit home"><Brand /></Link>
      <FormCtx.Provider value={{ f, set, file, dk, toggleDk }}>
      <form className="su-card" onSubmit={next}>
        <div className="stepper" aria-label={`Step ${step + 1} of ${STEPS.length}`}>
          {STEPS.map((s, i) => <div key={s} className={i < step ? 'done' : i === step ? 'now' : ''}><span>{s}</span></div>)}
        </div>

        <input ref={fileInput} type="file" accept=".csv" hidden onChange={(e) => setFile(e.target.files[0] || null)} />
        {step >= 1 && uploadBox(true)}

        {step === 0 && <>
          <div><h1>Create your ALTcredit profile</h1><p className="su-hint">No credit history needed. Use synthetic details only; this is a prototype.</p></div>
          <div className="su-grid">
            <div className="full"><Field k="full_name" core label="Full name" req maxLength={120} autoComplete="name" /></div>
            <div className="full"><Field k="email" core type="email" label="Email" req autoComplete="email" /></div>
            <Field k="password" core type="password" label="Password" hint="min 8 characters" req minLength={8} autoComplete="new-password" />
            <Field k="confirm" core type="password" label="Confirm password" req minLength={8} autoComplete="new-password" />
          </div></>}

        {step === 1 && <>
          <div><h1>About you</h1><p className="su-hint">Basic demographics that help place your finances in context.</p></div>
          <div className="su-grid">
            <Field k="age" type="number" min="18" max="100" label="Age" req />
            <Select k="city_tier" label="City tier" options={TIERS} req />
            <Select k="education_level" label="Highest education" options={EDU} req />
            <Select k="employment_status" label="Employment status" options={EMP} req />
            <div className="full"><Field k="monthly_income" type="number" min="0" step="any" label="Monthly income" hint="after tax, in your currency" req /></div>
          </div></>}

        {step === 2 && <>
          <div><h1>Work &amp; home stability</h1><p className="su-hint">Stability is one of the strongest signals when there’s no credit history.</p></div>
          <div className="su-grid">
            <Field k="months_at_job" type="number" min="0" label="Months at current job / gig platform" hint="roughly is fine" />
            <Select k="housing" label="Housing" options={[['owner', 'I own my home'], ['rent', 'I rent'], ['none', 'No stable address']]} req />
            {f.housing === 'rent' && <Field k="rent_on_time_months" type="number" min="0" label="Months of on-time rent" hint="roughly is fine" />}
            <Select k="digital_pct" label="Do you pay mobile / internet bills on time?" hint="last 12 months" options={ALWAYS} />
          </div></>}

        {step === 3 && <>
          <div><h1>Your money habits</h1><p className="su-hint">All optional, and approximate answers are fine. Choose “I don’t know” for anything you’re unsure of; it’s scored conservatively and shown as missing. Or upload a bank statement instead.</p></div>
          <div className="su-grid">
            <Field k="monthly_spend" type="number" min="0" step="any" label="Typical monthly spending" hint="a rough figure is fine" />
            <Select k="essential_pct" label="How much of your money goes on basics?" hint="food, rent, utilities" options={ESSENTIAL} />
            <Select k="savings_days" label="If your income stopped, how long could you cope?" hint="emergency savings" options={SAVINGS} />
            <Select k="on_time_pct" label="Do you pay all your bills and EMIs on time?" hint="last 12 months" options={ALWAYS} />
            <Select k="volatility" label="Does your income change month to month?" options={VOLATILITY} />
            <Select k="dti_pct" label="How much of your income goes on loan / EMI payments?" options={EMI} />
            <Select k="util_pct" label="How much of your credit card limit do you use?" hint="skip if you have no card" options={CARD_USE} />
            <Select k="late" label="Have you ever paid a bill late? (24 months)" options={LATE} />
            <Select k="positive_habits" label="Good money habits you follow" hint="saving regularly, budgeting app, giving to charity" options={HABITS} />
            <Select k="risk_flags" label="Recent warning signs" hint="moved house often, many loan or card applications" options={FLAGS} />
            <label className="full row" style={{ alignItems: 'flex-start' }}>
              <input type="checkbox" checked={f.share_with_lenders} onChange={(e) => setF({ ...f, share_with_lenders: e.target.checked })} />
              <span><strong>Let lenders find me (optional)</strong><br /><small>Lenders see an anonymous ID, your score and income band — never your name or email — and can send offers. They only learn who you are if you accept one. You can switch this off any time on your dashboard.</small></span>
            </label>
            <div className="full">{uploadBox(false)}</div>
          </div></>}

        {err && <div className="err" role="alert">{err}</div>}
        <div className="su-actions">
          {step > 0 ? <button type="button" className="btn btn-ghost" onClick={() => { setErr(''); setStep(step - 1) }}>Back</button> : <Link className="btn btn-ghost" to="/login">I have an account</Link>}
          {file && step >= 1 && step < STEPS.length - 1 && <button type="button" className="btn btn-tint" disabled={busy} onClick={submit}>Skip the rest &amp; get scored</button>}
          <button className="btn btn-primary" disabled={busy}>{busy ? 'Creating…' : step < STEPS.length - 1 ? 'Continue' : 'Create profile & get scored'} <Icon name="arrow_forward" /></button>
        </div>
      </form>
      </FormCtx.Provider>
    </div>
  )
}
