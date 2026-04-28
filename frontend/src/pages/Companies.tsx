import {
  CreateButton,
  DeleteButton,
  EditButton,
  List,
  useTable,
} from "@refinedev/antd";
import { useCreate, useDelete } from "@refinedev/core";
import {
  Form,
  Input,
  Modal,
  Select,
  Space,
  Table,
  Tag,
} from "antd";
import { useState } from "react";

const STANDARDS = ["PCG", "IFRS", "US_GAAP", "BE_GAAP", "DE_HGB", "UK_FRS102", "CH_FER", "ES_PGC", "IT_OIC", "NL_BW2", "PL_PSR", "LU_GAAP"];

export const CompanyList = () => {
  const { tableProps } = useTable({ resource: "companies", syncWithLocation: true });
  const { mutate: create } = useCreate();
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();

  const handleCreate = () => {
    form.validateFields().then((values) => {
      create({ resource: "companies", values }, { onSuccess: () => { setOpen(false); form.resetFields(); } });
    });
  };

  return (
    <>
      <List
        resource="companies"
        headerButtons={<CreateButton onClick={() => setOpen(true)}>Nouvelle société</CreateButton>}
      >
        <Table {...tableProps} rowKey="id" size="small">
          <Table.Column dataIndex="name" title="Raison sociale" />
          <Table.Column dataIndex="siren" title="SIREN" width={110} />
          <Table.Column dataIndex="legal_form" title="Forme" width={80} />
          <Table.Column
            dataIndex="accounting_standard"
            title="Référentiel"
            width={100}
            render={(v) => <Tag color="blue">{v}</Tag>}
          />
          <Table.Column dataIndex="city" title="Ville" width={120} />
          <Table.Column
            title="Actions"
            width={100}
            render={(_, record: { id: string }) => (
              <Space>
                <EditButton hideText size="small" recordItemId={record.id} />
                <DeleteButton hideText size="small" recordItemId={record.id} />
              </Space>
            )}
          />
        </Table>
      </List>

      <Modal title="Nouvelle société" open={open} onOk={handleCreate} onCancel={() => setOpen(false)} okText="Créer">
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="Raison sociale" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="siren" label="SIREN">
            <Input maxLength={9} />
          </Form.Item>
          <Form.Item name="legal_form" label="Forme juridique" initialValue="SAS">
            <Select options={["SAS","SARL","SASU","EURL","SA","EI"].map((v) => ({ value: v, label: v }))} />
          </Form.Item>
          <Form.Item name="accounting_standard" label="Référentiel" initialValue="PCG">
            <Select options={STANDARDS.map((v) => ({ value: v, label: v }))} />
          </Form.Item>
          <Form.Item name="city" label="Ville">
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};
