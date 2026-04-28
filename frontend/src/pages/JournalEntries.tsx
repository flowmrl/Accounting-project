import { List, useTable } from "@refinedev/antd";
import { Table, Tag, Typography } from "antd";

const statusColor: Record<string, string> = {
  BROUILLON: "orange",
  VALIDE: "green",
  CLOTURE: "blue",
  EXTOURNE: "red",
};

export const JournalEntryList = () => {
  const { tableProps } = useTable({
    resource: "journal-entries",
    syncWithLocation: true,
    sorters: { initial: [{ field: "entry_date", order: "desc" }] },
  });

  return (
    <List resource="journal-entries" title="Journal des écritures">
      <Table {...tableProps} rowKey="id" size="small">
        <Table.Column dataIndex="entry_date" title="Date" width={110} />
        <Table.Column dataIndex="entry_number" title="N°" width={110} />
        <Table.Column dataIndex="reference" title="Référence" width={130} />
        <Table.Column dataIndex="label" title="Libellé" ellipsis />
        <Table.Column
          dataIndex="status"
          title="Statut"
          width={110}
          render={(s: string) => <Tag color={statusColor[s] ?? "default"}>{s}</Tag>}
        />
      </Table>
    </List>
  );
};
