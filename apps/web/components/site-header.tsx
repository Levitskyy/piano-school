import { SiteHeaderNav } from "@/components/site-header-nav";
import { getCurrentUser } from "@/lib/auth";

export async function SiteHeader() {
  const user = await getCurrentUser();

  return (
    <header className="site-header">
      <a className="skip-link" href="#main-heading">
        Перейти к содержанию
      </a>
      <SiteHeaderNav user={user} />
    </header>
  );
}
