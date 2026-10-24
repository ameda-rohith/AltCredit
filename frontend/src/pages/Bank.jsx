import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../auth'
import { Brand } from '../components/Layout'
import { ThemeToggle } from '../components/ThemeToggle'
import { ErrorBox, Icon, fmt, useLoad } from '../components/ui'
import { bankFor } from '../banks'
import './bank.css'

const STEPS = ['Verifying the referral from ALTcredit', 'Checking eligibility against product rules', 'Preparing your pre-approved offer']
const LABELS = { credit_limit: 'Credit limit', approved_amount: 'Approved amount', tenure_months: 'Tenure (months)' }
const money = (k, v) => (typeof v === 'number' ? (k === 'tenure_months' ? fmt(v) : `₹${fmt(v)}`) : v)

function Mark({ id }) {
  // simple geometric marks, one per bank
  if (id === 'sentinel') return <svg viewBox="0 0 48 48" aria-hidden="true"><circle cx="24" cy="24" r="22" fill="currentColor" /><circle cx="24" cy="24" r="8" fill="#fff" /><rect x="22" y="26" width="4" height="16" rx="2" fill="#fff" /></svg>
  if (id === 'pinnacle') return <svg viewBox="0 0 48 48" aria-hidden="true"><rect x="3" y="3" width="42" height="42" fill="currentColor" /><rect x="15" y="15" width="18" height="18" fill="#e1251b" /></svg>
  return <svg viewBox="0 0 48 48" aria-hidden="true"><path d="M24 3 45 40H3z" fill="currentColor" /><path d="M24 17 34 36H14z" fill="#fff" /></svg>
}

function Header({ bank }) {
  const logo = <div className="bk-logo"><span className="bk-mark"><Mark id={bank.id} /></span><span><b>{bank.name}</b><small>{bank.tag}</small></span></div>
  const nav = <nav className="bk-nav" aria-hidden="true">{bank.nav.map((n) => <span key={n}>{n}</span>)}</nav>
  if (bank.id === 'sentinel') return (
    <header>
      <div className="bk-util"><div className="bk-wrap"><span>Personal Banking &nbsp;|&nbsp; Corporate &nbsp;|&nbsp; NRI</span><span>Customer care 1800 000 0000 &nbsp;|&nbsp; A- A A+</span></div></div>
      <div className="bk-top"><div className="bk-wrap">{logo}<span className="bk-secure"><Icon name="lock" />Secure session</span></div></div>
      <div className="bk-bar"><div className="bk-wrap">{nav}</div></div>
    </header>)
  return (
    <header className="bk-top"><div className="bk-wrap">{logo}{nav}<span className="bk-secure"><Icon name="lock" />Secure</span></div></header>)
}

function Shell({ bank, title, sub, crumb, children }) {
  return (
    <div className={`bank-page bk-${bank.id}`}>
      <Header bank={bank} />
      <div className="bk-refer"><div className="bk-wrap"><Icon name="swap_horiz" /> You were referred by <b>ALTcredit</b>. This is a simulated partner bank used for demonstration; no real application is made.</div></div>
      <section className="bk-hero"><div className="bk-wrap"><span className="bk-crumb">{crumb}</span><h1>{title}</h1><p>{sub}</p></div></section>
      <main className="bk-wrap bk-body">{children}</main>
      <footer className="bk-foot"><div className="bk-wrap"><b>{bank.name}</b> is a fictional bank created for the ALTcredit prototype. Rates and limits are indicative, synthetic and not an offer of credit.</div></footer>
    </div>)
}

function Redirect({ bank, error }) {
  return (
    <div className="auth">
      <ThemeToggle className="theme-fab" />
      <div className="auth-card bk-redirect">
        <Brand />
        {error ? <ErrorBox error={error} /> : <>
          <div className="bk-hand"><span className="bk-hand-a"><Icon name="trending_up" /></span><i /><i /><i /><span className={`bk-hand-b bk-${bank.id}`}><span className="bk-mark"><Mark id={bank.id} /></span></span></div>
          <h1>Taking you to {bank.name}</h1>
          <p>You are leaving ALTcredit for our partner bank to complete your application. Only your score, monthly income and anonymous applicant ID are shared. Never your name or account number.</p>
          <div className="bk-loadbar"><div /></div>
        </>}
      </div>
    </div>)
}

export default function Bank() {
  const { productId } = useParams()
  const { userId } = useAuth()
  const nav = useNavigate()
  const bank = bankFor(productId)
  const { data, error } = useLoad(() => Promise.all([api.products(), api.score(userId)]), [userId])
  const [stage, setStage] = useState('redirect')   // redirect → review → processing → result
  const [agree, setAgree] = useState(false)
  const [step, setStep] = useState(0)
  const [outcome, setOutcome] = useState(null)     // { result } | { error }
  const [waited, setWaited] = useState(false)

  useEffect(() => { const t = setTimeout(() => setWaited(true), 2200); return () => clearTimeout(t) }, [])
  useEffect(() => { if (stage === 'redirect' && waited && data) setStage('review') }, [stage, waited, data])

  const product = data?.[0]?.find((p) => p.product_id === productId)
  const score = data?.[1]
  if (error || (data && !product)) return <Redirect bank={bank} error={error || new Error('This product is no longer available.')} />
  if (stage === 'redirect' || !product) return <Redirect bank={bank} />

  const back = () => nav('/recommendations')
  const submit = async () => {
    setStage('processing'); setStep(0)
    const t0 = Date.now()
    const timers = [setTimeout(() => setStep(1), 700), setTimeout(() => setStep(2), 1400)]
    let out
    try { out = { result: await api.apply(userId, product.product_id) } } catch (e) { out = { error: e.message } }
    setTimeout(() => { timers.forEach(clearTimeout); setOutcome(out); setStage('result') }, Math.max(0, 2100 - (Date.now() - t0)))
  }
  const kind = product.type === 'Credit Card' ? 'Credit card' : 'Loan'
  const approved = outcome?.result?.status === 'APPROVED'

  if (stage === 'result') return (
    <Shell bank={bank} crumb={`Home › ${kind}s › Application status`} title={approved ? 'Your application is pre-approved' : 'Application status'} sub={product.product_name}>
      <section className={`bk-card bk-result ${approved ? 'ok' : 'no'}`}>
        <div className="bk-badge"><Icon name={approved ? 'check_circle' : 'info'} /></div>
        {approved ? <>
          <h2>Congratulations!</h2>
          <p>{outcome.result.already_applied ? 'You already hold an approved application for this product.' : `${bank.name} has pre-approved your ${product.product_name} application.`}</p>
          <dl className="bk-dl">
            {Object.entries(outcome.result.details || {}).map(([k, v]) => <div key={k}><dt>{LABELS[k] || k.replace(/_/g, ' ')}</dt><dd className="bk-big">{money(k, v)}</dd></div>)}
            <div><dt>Indicative rate</dt><dd>{product.interest_rate}</dd></div>
            <div><dt>Reference number</dt><dd className="bk-ref">{outcome.result.bank_reference}</dd></div>
          </dl>
        </> : <>
          <h2>We couldn’t pre-approve this</h2>
          <p>{outcome?.error || outcome?.result?.reason || 'The request was not approved.'}</p>
        </>}
        <div className="bk-actions"><button className="bk-btn" onClick={back}>Return to ALTcredit</button></div>
      </section>
    </Shell>)

  if (stage === 'processing') return (
    <Shell bank={bank} crumb={`Home › ${kind}s › Processing`} title="Processing your application" sub="Please don’t close or refresh this page.">
      <section className="bk-card bk-proc">
        <ol>{STEPS.map((s, i) => <li key={s} className={i < step ? 'done' : i === step ? 'now' : ''}><span className="bk-tick">{i < step ? <Icon name="check" /> : <i />}</span>{s}</li>)}</ol>
        <div className="bk-loadbar"><div /></div>
      </section>
    </Shell>)

  return (
    <Shell bank={bank} crumb={`Home › ${kind}s › ${product.product_name}`} title={product.product_name} sub={`Review your details and submit your pre-approved ${kind.toLowerCase()} application.`}>
      <div className="bk-grid">
        <section className="bk-card">
          <h2>Application summary</h2>
          <dl className="bk-dl">
            <div><dt>Product</dt><dd>{product.product_name}</dd></div>
            <div><dt>Type</dt><dd>{product.type}</dd></div>
            <div><dt>Indicative rate</dt><dd>{product.interest_rate}</dd></div>
            <div><dt>Minimum score</dt><dd>{product.min_score}</dd></div>
            <div><dt>Applicant ID</dt><dd>{userId}</dd></div>
            <div><dt>ALTcredit score</dt><dd>{fmt(score?.credit_score)}</dd></div>
          </dl>
        </section>
        <aside className="bk-card">
          <h2>Submit application</h2>
          <p className="bk-note">We will check your referral from ALTcredit and respond instantly. This is a soft check and does not affect any bureau score.</p>
          <label className="bk-check"><input type="checkbox" checked={agree} onChange={(e) => setAgree(e.target.checked)} /> I agree to share my ALTcredit score and monthly income with {bank.name} for this application.</label>
          <div className="bk-actions">
            <button className="bk-btn" disabled={!agree} onClick={submit}>{bank.cta}</button>
            <button className="bk-link" onClick={back}>Cancel and return to ALTcredit</button>
          </div>
        </aside>
      </div>
    </Shell>)
}
