import { Card, Col, Row, Statistic, Table, Tag, Typography } from "antd";
import {
  BankOutlined,
  EuroOutlined,
  FileTextOutlined,
  RiseOutlined,
} from "@ant-design/icons";
import { useList } from "@refinedev/core";

const { Title } = Typography;

export const Dashboard = () => {
  const { data: companies } = useList({ resource: "companies", pagination: { pageSize: 5 } });
  const { data: entries } = useList({
    resource: "journal-entries",
    pagination: { pageSize: 5 },
    sorters: [{ field: "entry_date", order: "desc" }],
  });

  const entryColumns = [
    { title: "Date", dataIndex: "entry_date", key: "date", width: 110 },
    { title: "Référence", dataIndex: "reference", key: "ref", width: 130 },
    { title: "Libellé", dataIndex: "label", key: "label", ellipsis: true },
    {
      title: "Statut",
      dataIndex: "status",
      key: "status",
      width: 100,
      render: (s: string) => (
        <Tag color={s === "VALIDE" ? "green" : s === "BROUILLON" ? "orange" : "blue"}>{s}</Tag>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Title level={3}>Tableau de bord</Title>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Sociétés"
              value={companies?.total ?? "—"}
              prefix={<BankOutlined />}
              valueStyle={{ color: "#1677ff" }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Écritures ce mois"
              value={entries?.total ?? "—"}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: "#52c41a" }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Référentiels"
              value={12}
              prefix={<RiseOutlined />}
              suffix="standards"
              valueStyle={{ color: "#722ed1" }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Devise principale"
              value="EUR"
              prefix={<EuroOutlined />}
              valueStyle={{ color: "#fa8c16" }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={14}>
          <Card title="Dernières écritures" size="small">
            <Table
              dataSource={entries?.data ?? []}
              columns={entryColumns}
              rowKey="id"
              size="small"
              pagination={false}
              locale={{ emptyText: "Aucune écriture" }}
            />
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card title="Sociétés actives" size="small">
            <Table
              dataSource={companies?.data ?? []}
              columns={[
                { title: "Nom", dataIndex: "name", key: "name", ellipsis: true },
                { title: "SIREN", dataIndex: "siren", key: "siren", width: 110 },
                { title: "Réf.", dataIndex: "accounting_standard", key: "std", width: 60 },
              ]}
              rowKey="id"
              size="small"
              pagination={false}
              locale={{ emptyText: "Aucune société" }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};
