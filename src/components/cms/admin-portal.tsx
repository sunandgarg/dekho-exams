import { useEffect } from "react";

const cmsUrl = import.meta.env["VITE_WORDPRESS_URL"]?.replace(/\/$/, "") || "https://cms.pencil2pen.com";

export function AdminPortal() {
  useEffect(() => {
    if (cmsUrl) window.location.replace(`${cmsUrl}/wp-admin/`);
  }, []);
  return <div className="mx-auto max-w-xl px-5 py-24 text-center">
    <h1 className="font-display text-3xl font-bold">WordPress editor</h1>
    <p className="mt-4">Opening the WordPress dashboard… <a className="text-primary underline" href={`${cmsUrl}/wp-admin/`}>Open it now</a>.</p>
  </div>;
}
