'use client';

import { useState } from 'react';

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ status: string; message: string } | null>(null);

  const triggerAudit = async () => {
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch('/api/audit', {
        method: 'POST',
      });
      const data = await res.json();
      setResult(data);
    } catch (error: any) {
      setResult({ status: 'error', message: error.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-brand-body flex flex-col items-center justify-center p-6 relative overflow-hidden">
      {/* Decorative background elements */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-brand-primary/10 blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-brand-highlight/10 blur-[120px] rounded-full pointer-events-none" />
      
      <main className="z-10 flex flex-col items-center max-w-3xl w-full text-center space-y-8">
        {/* Header area */}
        <div className="space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-highlight/10 border border-brand-highlight/30 text-brand-primary text-sm font-semibold">
            <span className="w-2 h-2 rounded-full bg-brand-highlight animate-pulse"></span>
            Tatvic GA4 Security
          </div>
          <h1 className="text-5xl md:text-6xl font-bold tracking-tight text-brand-headline">
            GA4 PII Auditor
          </h1>
          <p className="text-brand-body text-lg md:text-xl max-w-2xl mx-auto leading-relaxed">
            Monitor and detect Personally Identifiable Information leaks across your Google Analytics 4 properties instantly.
          </p>
        </div>

        <div className="p-8 bg-white border border-brand-border rounded-3xl shadow-xl w-full max-w-xl transition-all duration-300 hover:border-brand-primary/20">
          <button
            onClick={triggerAudit}
            disabled={loading}
            className={`w-full py-4 px-6 rounded-2xl font-bold text-lg flex items-center justify-center gap-3 transition-all duration-300 transform hover:scale-[1.02] active:scale-[0.98] ${
              loading 
                ? 'bg-brand-border text-brand-body cursor-not-allowed' 
                : 'bg-brand-primary hover:bg-brand-primary/90 text-white shadow-lg shadow-brand-primary/25'
            }`}
          >
            {loading ? (
              <>
                <svg className="animate-spin h-5 w-5 text-current" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Auditing in Progress...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                Run Manual Audit Now
              </>
            )}
          </button>

          {result && (
            <div className={`mt-6 p-4 rounded-xl flex items-start gap-3 animate-in fade-in slide-in-from-bottom-4 duration-500 ${
              result.status === 'success' 
                ? 'bg-brand-success/10 border border-brand-success/20 text-brand-success' 
                : 'bg-brand-error/10 border border-brand-error/20 text-brand-error'
            }`}>
              {result.status === 'success' ? (
                <svg className="w-6 h-6 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
              ) : (
                <svg className="w-6 h-6 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
              )}
              <div className="text-left">
                <h3 className="font-semibold">{result.status === 'success' ? 'Audit Complete' : 'Audit Failed'}</h3>
                <p className="text-sm mt-1 opacity-80">{result.message}</p>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
