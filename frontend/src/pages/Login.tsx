import { AuthPage } from "@refinedev/antd";

export const Login = () => (
  <AuthPage
    type="login"
    title="Compta PME"
    formProps={{
      initialValues: { username: "admin", password: "admin" },
    }}
  />
);
