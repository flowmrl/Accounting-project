import {
  AccountBookOutlined,
  BankOutlined,
  DashboardOutlined,
  FileTextOutlined,
} from "@ant-design/icons";
import { Authenticated, Refine } from "@refinedev/core";
import { RefineThemes, ThemedLayoutV2, ThemedTitleV2, useNotificationProvider } from "@refinedev/antd";
import routerBindings, {
  CatchAllNavigate,
  DocumentTitleHandler,
  NavigateToResource,
  UnsavedChangesNotifier,
} from "@refinedev/react-router-v6";
import simpleRestDataProvider, { axiosInstance as refineAxios } from "@refinedev/simple-rest";
import { App as AntdApp, ConfigProvider } from "antd";
import frFR from "antd/locale/fr_FR";
import { BrowserRouter, Outlet, Route, Routes } from "react-router-dom";

import { authProvider } from "./providers/authProvider";
import { AccountList } from "./pages/Accounts";
import { CompanyList } from "./pages/Companies";
import { Dashboard } from "./pages/Dashboard";
import { JournalEntryList } from "./pages/JournalEntries";
import { Login } from "./pages/Login";

import "@refinedev/antd/dist/reset.css";

const API_URL = "/api/v1";

// Ajoute le Bearer token sur chaque requête
// Intercepteur Bearer token sur l'instance Axios interne de Refine
refineAxios.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token && config.headers) config.headers["Authorization"] = `Bearer ${token}`;
  return config;
});

const dataProvider = simpleRestDataProvider(API_URL);

function App() {
  const notificationProvider = useNotificationProvider();

  return (
    <BrowserRouter>
      <ConfigProvider theme={RefineThemes.Blue} locale={frFR}>
        <AntdApp>
          <Refine
            dataProvider={dataProvider}
            authProvider={authProvider}
            routerProvider={routerBindings}
            notificationProvider={notificationProvider}
            resources={[
              {
                name: "companies",
                list: "/companies",
                meta: { label: "Sociétés", icon: <BankOutlined /> },
              },
              {
                name: "accounts",
                list: "/accounts",
                meta: { label: "Plan de comptes", icon: <AccountBookOutlined /> },
              },
              {
                name: "journal-entries",
                list: "/journal-entries",
                meta: { label: "Journal", icon: <FileTextOutlined /> },
              },
            ]}
            options={{ syncWithLocation: true, warnWhenUnsavedChanges: true }}
          >
            <Routes>
              <Route
                element={
                  <Authenticated key="auth" fallback={<CatchAllNavigate to="/login" />}>
                    <ThemedLayoutV2
                      Title={({ collapsed }) => (
                        <ThemedTitleV2
                          collapsed={collapsed}
                          text="Compta PME"
                          icon={<DashboardOutlined />}
                        />
                      )}
                    >
                      <Outlet />
                    </ThemedLayoutV2>
                  </Authenticated>
                }
              >
                <Route index element={<NavigateToResource resource="dashboard" />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/companies" element={<CompanyList />} />
                <Route path="/accounts" element={<AccountList />} />
                <Route path="/journal-entries" element={<JournalEntryList />} />
              </Route>
              <Route path="/login" element={<Login />} />
            </Routes>
            <UnsavedChangesNotifier />
            <DocumentTitleHandler />
          </Refine>
        </AntdApp>
      </ConfigProvider>
    </BrowserRouter>
  );
}

export default App;
