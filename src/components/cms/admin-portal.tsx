import { useEffect } from "react";

const cmsUrl = import.meta.env["VITE_WORDPRESS_URL"]?.replace(/\/$/, "");

export function AdminPortal() {
  useEffect(() => {
    if (cmsUrl) window.location.replace(`${cmsUrl}/wp-admin/`);
  }, []);
  return <div className="mx-auto max-w-xl px-5 py-24 text-center">
    <h1 className="font-display text-3xl font-bold">WordPress editor</h1>
    {cmsUrl ? <p className="mt-4">Opening the WordPress dashboard… <a className="text-primary underline" href={`${cmsUrl}/wp-admin/`}>Open it now</a>.</p> :
      <p className="mt-4 text-muted-foreground">The WordPress CMS address has not been connected yet. Set WORDPRESS_URL and VITE_WORDPRESS_URL in the deployment environment to enable editing.</p>}
  </div>;
}
