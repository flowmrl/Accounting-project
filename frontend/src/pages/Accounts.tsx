import { List, useTable } from "@refinedev/antd";
import { Input, Table, Tag } from "antd";
import { useState } from "react";

const natureColor: Record<string, string> = {
  ACTIF: "blue",
  PASSIF: "purple",
  CHARGE: "red",
  PRODUIT: "green",
  BILAN: "cyan",
  RESULTAT: "orange",
};

export const AccountList = () => {
  const [search, setSearch] = useState("");
  const { tableProps } = useTable({
    resource: "accounts",
    syncWithLocation: true,
    filters: {
      permanent: search ? [{ field: "search", operator: "contains", value: search }] : [],
    },
  });

  return (
    <List resource="accounts" title="Plan de comptes">
      <Input.Search
        placeholder="Rechercher un compte (code ou intitulé)…"
        allowClear
        onSearch={setSearch}
        style={{ marginBottom: 16, maxWidth: 400 }}
      />
      <Table {...tableProps} rowKey="id" size="small">
        <Table.Column dataIndex="code" title="Code" width={100} sorter />
        <Table.Column dataIndex="name" title="Intitulé" ellipsis />
        <Table.Column
          dataIndex="account_nature"
          title="Nature"
          width={100}
          render={(n: string) => <Tag color={natureColor[n] ?? "default"}>{n}</Tag>}
        />
        <Table.Column
          dataIndex="is_detail"
          title="Détail"
          width={80}
          render={(v: boolean) => <Tag color={v ? "green" : "default"}>{v ? "Oui" : "Non"}</Tag>}
        />
      </Table>
    </List>
  );
};
