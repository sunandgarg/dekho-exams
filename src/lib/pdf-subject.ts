// Use the same canonical subject segment in the router, directory links and sitemap.
export const pdfSubjectSlug = (subject: string) => subject.toLowerCase().trim().replace(/\s+/g, "-");
