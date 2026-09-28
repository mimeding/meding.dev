// Send www.meding.dev to meding.dev with a permanent redirect, keeping path and query.
export async function onRequest(context) {
  const url = new URL(context.request.url);
  if (url.hostname === 'www.meding.dev') {
    url.hostname = 'meding.dev';
    return Response.redirect(url.toString(), 301);
  }
  return context.next();
}
