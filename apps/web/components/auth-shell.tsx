import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";

type AuthShellProps = {
  eyebrow: string;
  title: string;
  lead: string;
  children: React.ReactNode;
  aside?: React.ReactNode;
};

export function AuthShell({ eyebrow, title, lead, children, aside }: AuthShellProps) {
  return (
    <div className="site">
      <SiteHeader />
      <main className="auth-page">
        <section className="auth-intro" aria-labelledby="main-heading">
          <p className="eyebrow">{eyebrow}</p>
          <h1 id="main-heading" tabIndex={-1}>
            {title}
          </h1>
          <p className="lead">{lead}</p>
          {aside ? <div className="auth-aside">{aside}</div> : null}
        </section>

        <div className="auth-card">{children}</div>
      </main>
      <SiteFooter />
    </div>
  );
}
