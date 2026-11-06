declare module "cloudflare:workers" {
  export const env: {
    SCHOOL_WORDPRESS_URL?: string;
    ASSETS: { fetch(request: Request): Promise<Response> };
  };
}
