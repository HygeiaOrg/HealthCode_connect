import { useRef, useState } from 'react'
import { uploadInvoicePdf, type UploadResult } from '../api/client'

export function UploadCard() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [drag, setDrag] = useState(false)
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState<UploadResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const check = async (file: File) => {
    setBusy(true)
    setError(null)
    setResult(null)
    try {
      setResult(await uploadInvoicePdf(file))
    } catch {
      setError('Could not reach the validation service. Start the backend (uvicorn on port 8000) and try again.')
    } finally {
      setBusy(false)
    }
  }

  const parsed = result?.parsed
  const who = parsed
    ? [parsed.patient?.first_name, parsed.patient?.surname].filter(Boolean).join(' ')
    : null

  return (
    <div className="card">
      <div className="row spread">
        <b>Check an invoice before it goes anywhere</b>
        <span className="footnote">PDF in, verdict out. Deterministic; sample PDFs live in backend/samples/.</span>
      </div>
      <div
        className={`dropzone section-gap${drag ? ' drag' : ''}`}
        style={{ marginTop: 12 }}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDrag(false)
          const file = e.dataTransfer.files?.[0]
          if (file) void check(file)
        }}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) void check(file)
            e.target.value = ''
          }}
        />
        {busy ? 'Checking against the rulebook…' : <>Drop an invoice PDF here, or <b>browse</b></>}
      </div>

      {error && (
        <div className="vpanel">
          <div className="vpanel-head">{error}</div>
        </div>
      )}

      {result && result.valid && (
        <div className="result-ok">
          ✓ {result.filename}: passes all checks
          <span className="sub">
            {who && `${who} · `}
            {parsed?.policy?.insurer_id} · net £{parsed?.totals?.net}
            {' '}· ready to submit to Medserv
          </span>
        </div>
      )}

      {result && !result.valid && (
        <>
          <div className="vpanel">
            <div className="vpanel-head">
              {result.filename}: {result.issues.length} issue{result.issues.length === 1 ? '' : 's'} found —
              fix before submission
            </div>
            {result.issues.map((issue, i) => (
              <div className="vrow" key={i}>
                <span className="f"><span className="vlbl">Field</span>{issue.field}</span>
                <span><span className="vlbl">Error</span>{issue.error}</span>
                <span className="s"><span className="vlbl">Solution</span>{issue.solution}</span>
              </div>
            ))}
          </div>
          {who && (
            <div className="result-meta">
              Parsed: {who} · {parsed?.policy?.insurer_id} · net £{parsed?.totals?.net ?? '?'}
            </div>
          )}
        </>
      )}
    </div>
  )
}
