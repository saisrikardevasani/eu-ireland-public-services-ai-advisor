import Link from "next/link";
import Image from "next/image";

export const metadata = {
  title: "Privacy Notice — Ireland Public Services AI Advisor",
  description: "How your data is handled when you use this service.",
};

const LAST_UPDATED = "18 June 2025";
const VERSION = "1.0";

function Section({ id, title, children }: { id: string; title: string; children: React.ReactNode }) {
  return (
    <section id={id} className="py-8 border-b border-stone-200 last:border-0">
      <h2 className="font-serif text-xl text-stone-900 mb-4">{title}</h2>
      <div className="space-y-3 text-stone-600 text-sm leading-relaxed">{children}</div>
    </section>
  );
}

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-cream-100 font-sans">

      {/* Nav */}
      <nav className="sticky top-0 z-50 bg-forest-800">
        <div className="max-w-3xl mx-auto px-6 h-14 flex items-center gap-4">
          <Link
            href="/"
            className="text-forest-300 hover:text-white transition-colors"
            aria-label="Back to home"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </Link>
          <div className="w-px h-5 bg-forest-600" />
          <Image src="/harp.svg" alt="Irish harp" width={12} height={19} className="opacity-60 brightness-0 invert" />
          <span className="font-serif text-white text-[0.95rem]">Ireland Public Services Advisor</span>
        </div>
      </nav>

      <main className="max-w-3xl mx-auto px-6 py-14">

        {/* Header */}
        <div className="mb-10">
          <p className="text-forest-600 text-xs font-semibold uppercase tracking-[0.15em] mb-3">Legal</p>
          <h1 className="font-serif text-4xl text-stone-950 mb-4">Privacy Notice</h1>
          <p className="text-stone-400 text-xs">
            Version {VERSION} · Last updated {LAST_UPDATED}
          </p>
          <p className="mt-4 text-stone-500 text-sm leading-relaxed">
            This notice explains how this service handles your information when you use the
            Ireland Public Services AI Advisor. It is written to comply with the{" "}
            <strong>EU General Data Protection Regulation (GDPR)</strong> and Ireland&apos;s{" "}
            <strong>Data Protection Acts 1988–2018</strong>, in particular Articles 13 and 14
            of the GDPR which require you to be informed about data processing.
          </p>
        </div>

        {/* TOC */}
        <nav className="mb-10 p-5 rounded-xl bg-white border border-stone-200">
          <p className="text-xs font-semibold text-stone-400 uppercase tracking-wider mb-3">Contents</p>
          <ol className="space-y-1.5 text-sm text-forest-700">
            {[
              ["#controller", "1. Who is the data controller"],
              ["#what-we-process", "2. What data is processed"],
              ["#legal-basis", "3. Legal basis for processing"],
              ["#third-parties", "4. Third-party processors and international transfers"],
              ["#retention", "5. Retention"],
              ["#your-rights", "6. Your rights"],
              ["#dpc", "7. How to complain"],
              ["#contact", "8. Contact"],
            ].map(([href, label]) => (
              <li key={href}>
                <a href={href} className="hover:text-forest-900 hover:underline transition-colors">{label}</a>
              </li>
            ))}
          </ol>
        </nav>

        <Section id="controller" title="1. Who is the data controller">
          <p>
            The data controller for this service is <strong>Sai Srikar Devasani</strong>, an individual
            developer based in Ireland. You can reach the controller at{" "}
            <a href="mailto:saisrikardevasani@gmail.com" className="underline text-forest-700 hover:text-forest-900">
              saisrikardevasani@gmail.com
            </a>.
          </p>
          <p>
            This service does not have a designated Data Protection Officer (DPO). If you have
            a data protection concern, contact the controller directly at the email above.
          </p>
        </Section>

        <Section id="what-we-process" title="2. What data is processed when you use this service">
          <p>
            <strong>Data you provide:</strong> When you type a question into the chat interface, that
            question text is processed to generate a response. We strongly advise you not to include
            personal information such as your PPS number, date of birth, address, income figures,
            health information, or other sensitive personal data in your questions. Phrase queries in
            general terms (e.g. &ldquo;What is the VAT registration threshold?&rdquo; rather than
            including personal identifiers).
          </p>
          <p>
            <strong>Data we do not collect or store:</strong> This service does not log, store, or
            retain your questions, answers, or session history in any database operated by the
            controller. No user accounts are created. No cookies are set by this service for
            tracking purposes.
          </p>
          <p>
            <strong>Technical data:</strong> Standard web server logs (IP address, timestamp,
            HTTP method, response code) may be recorded by our hosting provider (Vercel) and
            the backend hosting provider (Hugging Face) for infrastructure security and
            reliability purposes. These are governed by their respective privacy policies.
          </p>
        </Section>

        <Section id="legal-basis" title="3. Legal basis for processing">
          <p>
            Processing your question text to generate a response is necessary to perform the
            service you request. The legal basis is <strong>Article 6(1)(b) GDPR</strong> —
            processing necessary for the performance of a contract (or steps taken at your
            request prior to a contract), specifically the provision of this information service.
          </p>
          <p>
            Where your query is transmitted to NVIDIA&apos;s API (see Section 4), this
            constitutes a transfer to a third-country processor. The legal basis for that
            transfer is <strong>Article 46(2)(c) GDPR</strong> — standard contractual clauses
            incorporated into NVIDIA&apos;s data processing terms, and NVIDIA&apos;s certification
            under the EU–US Data Privacy Framework (DPF), which provides an adequacy-equivalent
            mechanism for US transfers.
          </p>
        </Section>

        <Section id="third-parties" title="4. Third-party processors and international transfers">
          <p className="font-medium text-stone-800">
            The following sub-processors handle data as part of this service:
          </p>

          <div className="overflow-x-auto mt-2">
            <table className="w-full text-xs border border-stone-200 rounded-lg overflow-hidden">
              <thead className="bg-stone-50 text-stone-600 font-semibold">
                <tr>
                  <th className="text-left px-3 py-2">Processor</th>
                  <th className="text-left px-3 py-2">Purpose</th>
                  <th className="text-left px-3 py-2">Location</th>
                  <th className="text-left px-3 py-2">Transfer mechanism</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100 text-stone-600">
                <tr>
                  <td className="px-3 py-2 font-medium">NVIDIA Corporation</td>
                  <td className="px-3 py-2">LLM inference (answer generation)</td>
                  <td className="px-3 py-2">United States</td>
                  <td className="px-3 py-2">EU–US DPF + SCCs</td>
                </tr>
                <tr className="bg-stone-50">
                  <td className="px-3 py-2 font-medium">Vercel Inc.</td>
                  <td className="px-3 py-2">Frontend hosting</td>
                  <td className="px-3 py-2">United States (EU CDN edge)</td>
                  <td className="px-3 py-2">SCCs</td>
                </tr>
                <tr>
                  <td className="px-3 py-2 font-medium">Hugging Face Inc.</td>
                  <td className="px-3 py-2">Backend (RAG pipeline) hosting</td>
                  <td className="px-3 py-2">United States</td>
                  <td className="px-3 py-2">SCCs</td>
                </tr>
                <tr className="bg-stone-50">
                  <td className="px-3 py-2 font-medium">Supabase Inc.</td>
                  <td className="px-3 py-2">Knowledge base database (no user queries stored)</td>
                  <td className="px-3 py-2">EU West (Ireland)</td>
                  <td className="px-3 py-2">Within EEA — no transfer</td>
                </tr>
                <tr>
                  <td className="px-3 py-2 font-medium">Upstash Inc.</td>
                  <td className="px-3 py-2">Query result cache (no PII stored)</td>
                  <td className="px-3 py-2">EU West</td>
                  <td className="px-3 py-2">Within EEA — no transfer</td>
                </tr>
              </tbody>
            </table>
          </div>

          <p>
            <strong>Important:</strong> When you send a question, that question text is transmitted
            to NVIDIA&apos;s API to generate a response. NVIDIA processes it in the United States.
            You should not include sensitive personal data in your questions. See{" "}
            <a
              href="https://www.nvidia.com/en-us/about-nvidia/privacy-policy/"
              target="_blank"
              rel="noopener noreferrer"
              className="underline text-forest-700 hover:text-forest-900"
            >
              NVIDIA&apos;s Privacy Policy
            </a>{" "}
            for details of how they handle inference requests.
          </p>
        </Section>

        <Section id="retention" title="5. Retention">
          <p>
            Your question text is not stored by this service. It is transmitted to NVIDIA&apos;s
            API and discarded after the response is generated. NVIDIA&apos;s own retention policy
            applies to any data it may log for service operation — see their privacy policy.
          </p>
          <p>
            The knowledge base (official Irish guidance documents) is retained indefinitely and
            updated periodically as source websites are re-crawled. This data is derived from
            publicly available official government guidance and contains no personal data.
          </p>
          <p>
            Infrastructure logs held by Vercel and Hugging Face are subject to their own
            standard retention periods (typically 30–90 days).
          </p>
        </Section>

        <Section id="your-rights" title="6. Your rights under GDPR">
          <p>Under the GDPR you have the following rights:</p>
          <ul className="space-y-2 pl-4">
            {[
              ["Right of access (Art. 15)", "You can request confirmation of whether we hold personal data about you and a copy of that data."],
              ["Right to rectification (Art. 16)", "You can ask us to correct inaccurate personal data."],
              ["Right to erasure (Art. 17)", "You can ask us to delete personal data we hold about you where there is no legitimate reason to continue processing it."],
              ["Right to restriction (Art. 18)", "You can ask us to restrict processing of your personal data in certain circumstances."],
              ["Right to data portability (Art. 20)", "You can request your personal data in a structured, machine-readable format where applicable."],
              ["Right to object (Art. 21)", "You can object to processing based on legitimate interests."],
            ].map(([right, desc]) => (
              <li key={right} className="flex gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-forest-400 mt-1.5 shrink-0" />
                <span><strong className="text-stone-800">{right}:</strong> {desc}</span>
              </li>
            ))}
          </ul>
          <p>
            Because this service does not store your questions, the practical effect of most of
            these rights in relation to query data is that there is nothing to access, correct,
            or erase. If you have a concern about infrastructure logs held by Vercel or Hugging
            Face, you should contact those processors directly.
          </p>
          <p>
            To exercise any right, contact the controller at{" "}
            <a href="mailto:saisrikardevasani@gmail.com" className="underline text-forest-700 hover:text-forest-900">
              saisrikardevasani@gmail.com
            </a>.
            We will respond within one month as required by Article 12 GDPR.
          </p>
        </Section>

        <Section id="dpc" title="7. How to complain">
          <p>
            If you are not satisfied with how we handle your personal data, you have the right to
            lodge a complaint with the Irish supervisory authority:
          </p>
          <div className="mt-3 p-4 rounded-lg bg-white border border-stone-200 text-sm">
            <p className="font-semibold text-stone-900">Data Protection Commission (DPC)</p>
            <p className="mt-1">21 Fitzwilliam Square South, Dublin 2, D02 RD28, Ireland</p>
            <p>
              <a href="https://www.dataprotection.ie" target="_blank" rel="noopener noreferrer" className="underline text-forest-700 hover:text-forest-900">
                www.dataprotection.ie
              </a>
            </p>
            <p>Phone: +353 (0)76 1104 800</p>
          </div>
          <p>
            You may also complain to the supervisory authority in the EU member state where you
            live or work, or where the alleged infringement occurred.
          </p>
        </Section>

        <Section id="contact" title="8. Contact">
          <p>
            For any question about this privacy notice or to exercise your rights, contact:
          </p>
          <div className="mt-2 p-4 rounded-lg bg-white border border-stone-200 text-sm">
            <p className="font-semibold text-stone-900">Sai Srikar Devasani (Data Controller)</p>
            <p>
              <a href="mailto:saisrikardevasani@gmail.com" className="underline text-forest-700 hover:text-forest-900">
                saisrikardevasani@gmail.com
              </a>
            </p>
          </div>
        </Section>

      </main>

      <footer className="bg-forest-800 mt-10">
        <div className="max-w-3xl mx-auto px-6 py-5 flex items-center justify-between gap-4">
          <Link href="/" className="text-sm text-forest-300 hover:text-white transition-colors">
            ← Back to home
          </Link>
          <p className="text-xs text-forest-400">
            Privacy Notice v{VERSION} · {LAST_UPDATED}
          </p>
        </div>
      </footer>
    </div>
  );
}
