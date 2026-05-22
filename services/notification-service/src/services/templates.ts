// Inline templates. Variables use {{varName}} substitution.
// All templates render to HTML; the email dispatcher wraps them in the standard
// FinsPoly mail chrome before sending.

export const TEMPLATES: Record<string, string> = {
  welcome:
    "<h1>Welcome, {{firstName}}!</h1><p>Your FinsPoly account has been created. Your reference id is <b>{{customerId}}</b>.</p>",

  password_reset:
    "<p>Hi {{firstName}},</p><p>Use this code to reset your password: <b>{{resetToken}}</b>. It expires in 15 minutes.</p>",

  txn_alert:
    "<p>A {{txnType}} of <b>{{amount}}</b> {{currency}} was posted to account {{accountNumber}} on {{postedAt}}.</p>",

  statement_ready:
    "<p>Your {{month}} statement for account {{accountNumber}} is ready. <a href=\"{{url}}\">View statement</a>.</p>",
};

const HTML_SHELL =
  "<html><body style=\"font-family:Arial,sans-serif\">{{body}}<hr/><small>FinsPoly Bank · do not reply</small></body></html>";

export function renderTemplate(name: string, vars: Record<string, unknown>): string {
  const tpl = TEMPLATES[name];
  if (!tpl) throw new Error(`unknown template: ${name}`);

  const body = tpl.replace(/{{(\w+)}}/g, (_, key) => {
    const v = vars[key];
    return v === undefined || v === null ? "" : String(v);
  });

  return HTML_SHELL.replace("{{body}}", body);
}
