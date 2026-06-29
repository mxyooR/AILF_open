import React, { useEffect } from 'react';
import { Modal, Form, Input, InputNumber, Switch, DatePicker, Select, Alert } from 'antd';
import { Entity, EntityField, EntityDataRecord } from '../../../types/developer/entity';
import dayjs from 'dayjs';

const { TextArea } = Input;

interface DynamicRecordFormProps {
  entity: Entity;
  record?: EntityDataRecord | null;
  visible: boolean;
  mode: 'create' | 'edit';
  loading?: boolean;
  onSubmit: (data: Record<string, any>) => Promise<void>;
  onCancel: () => void;
}

/**
 * 根据字段类型获取对应的表单控件
 */
const getFieldControl = (field: EntityField) => {
  const commonProps = {
    placeholder: `请输入${field.displayName}`,
    style: { width: '100%' },
  };

  switch (field.type) {
    case 'text':
      // 如果有最大长度限制且较大，使用TextArea
      if (field.validation?.max && field.validation.max > 200) {
        return <TextArea {...commonProps} rows={3} maxLength={field.validation.max} showCount />;
      }
      return <Input {...commonProps} maxLength={field.validation?.max} />;

    case 'number':
      return (
        <InputNumber
          {...commonProps}
          min={field.validation?.min}
          max={field.validation?.max}
          precision={0}
        />
      );

    case 'decimal':
      return (
        <InputNumber
          {...commonProps}
          min={field.validation?.min}
          max={field.validation?.max}
          precision={2}
          step={0.01}
        />
      );

    case 'boolean':
      return <Switch checkedChildren="是" unCheckedChildren="否" />;

    case 'date':
      return (
        <DatePicker
          {...commonProps}
          format="YYYY-MM-DD"
          placeholder={`请选择${field.displayName}`}
        />
      );

    case 'datetime':
      return (
        <DatePicker
          {...commonProps}
          showTime
          format="YYYY-MM-DD HH:mm:ss"
          placeholder={`请选择${field.displayName}`}
        />
      );

    case 'email':
      return <Input {...commonProps} type="email" placeholder={`请输入${field.displayName}`} />;

    case 'phone':
      return <Input {...commonProps} placeholder={`请输入${field.displayName}`} />;

    case 'select':
      return (
        <Select {...commonProps} placeholder={`请选择${field.displayName}`}>
          {field.options?.map((option) => (
            <Select.Option key={option} value={option}>
              {option}
            </Select.Option>
          ))}
        </Select>
      );

    case 'multiselect':
      return (
        <Select {...commonProps} mode="multiple" placeholder={`请选择${field.displayName}`}>
          {field.options?.map((option) => (
            <Select.Option key={option} value={option}>
              {option}
            </Select.Option>
          ))}
        </Select>
      );

    case 'reference':
      // 引用类型暂时用文本输入
      return <Input {...commonProps} placeholder={`请输入${field.displayName}的ID`} />;

    default:
      // 如果有options，渲染为Select
      if (field.options && field.options.length > 0) {
        return (
          <Select {...commonProps} placeholder={`请选择${field.displayName}`}>
            {field.options.map((option) => (
              <Select.Option key={option} value={option}>
                {option}
              </Select.Option>
            ))}
          </Select>
        );
      }
      return <Input {...commonProps} />;
  }
};

/**
 * 根据字段定义生成表单验证规则
 */
const getFieldRules = (field: EntityField) => {
  const rules: any[] = [];

  // 必填验证
  if (field.required) {
    rules.push({
      required: true,
      message: `${field.displayName}是必填项`,
    });
  }

  // 数值范围验证
  if (field.type === 'number' && field.validation) {
    if (field.validation.min !== undefined) {
      rules.push({
        type: 'number',
        min: field.validation.min,
        message: `${field.displayName}不能小于${field.validation.min}`,
      });
    }
    if (field.validation.max !== undefined) {
      rules.push({
        type: 'number',
        max: field.validation.max,
        message: `${field.displayName}不能大于${field.validation.max}`,
      });
    }
  }

  // 文本长度验证
  if (field.type === 'text' && field.validation) {
    if (field.validation.min !== undefined) {
      rules.push({
        min: field.validation.min,
        message: `${field.displayName}长度不能少于${field.validation.min}个字符`,
      });
    }
    if (field.validation.max !== undefined) {
      rules.push({
        max: field.validation.max,
        message: `${field.displayName}长度不能超过${field.validation.max}个字符`,
      });
    }
    // 正则验证
    if (field.validation.pattern) {
      rules.push({
        pattern: new RegExp(field.validation.pattern),
        message: field.validation.message || `${field.displayName}格式不正确`,
      });
    }
  }

  return rules;
};

/**
 * 将记录数据转换为表单值
 */
const recordToFormValues = (record: EntityDataRecord | null, fields: EntityField[]) => {
  if (!record) return {};

  const values: Record<string, any> = {};
  
  fields.forEach((field) => {
    const value = record[field.name];
    
    if (value === undefined || value === null) {
      values[field.name] = field.defaultValue;
      return;
    }

    // 日期类型需要转换为dayjs对象
    if ((field.type === 'date' || field.type === 'datetime') && value) {
      values[field.name] = dayjs(value);
    } else {
      values[field.name] = value;
    }
  });

  return values;
};

/**
 * 将表单值转换为提交数据
 */
const formValuesToRecord = (values: Record<string, any>, fields: EntityField[]) => {
  const data: Record<string, any> = {};

  fields.forEach((field) => {
    const value = values[field.name];

    if (value === undefined || value === null) {
      if (field.required) {
        data[field.name] = field.defaultValue || null;
      }
      return;
    }

    // 日期类型需要转换为ISO字符串
    if ((field.type === 'date' || field.type === 'datetime') && value) {
      data[field.name] = value.toISOString();
    } else {
      data[field.name] = value;
    }
  });

  return data;
};

const DynamicRecordForm: React.FC<DynamicRecordFormProps> = ({
  entity,
  record,
  visible,
  mode,
  loading,
  onSubmit,
  onCancel,
}) => {
  const [form] = Form.useForm();

  // 当记录变化时，重置表单
  useEffect(() => {
    if (visible) {
      if (mode === 'edit' && record) {
        const formValues = recordToFormValues(record, entity.fields || []);
        form.setFieldsValue(formValues);
      } else {
        // 创建模式，设置默认值
        const defaultValues: Record<string, any> = {};
        entity.fields?.forEach((field) => {
          if (field.defaultValue !== undefined) {
            defaultValues[field.name] = field.defaultValue;
          }
        });
        form.setFieldsValue(defaultValues);
      }
    }
  }, [visible, mode, record, entity.fields, form]);

  // 处理表单提交
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const data = formValuesToRecord(values, entity.fields || []);
      await onSubmit(data);
      form.resetFields();
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  // 处理取消
  const handleCancel = () => {
    form.resetFields();
    onCancel();
  };

  // 获取唯一字段列表
  const uniqueFields = entity.fields?.filter((f) => f.unique) || [];

  return (
    <Modal
      title={mode === 'create' ? `新建${entity.displayName}记录` : `编辑${entity.displayName}记录`}
      open={visible}
      onOk={handleSubmit}
      onCancel={handleCancel}
      confirmLoading={loading}
      okText={mode === 'create' ? '创建' : '保存'}
      cancelText="取消"
      width={600}
      destroyOnHidden
    >
      {uniqueFields.length > 0 && (
        <Alert
          message="唯一字段提示"
          description={`以下字段要求唯一：${uniqueFields.map((f) => f.displayName).join('、')}`}
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      <Form
        form={form}
        layout="vertical"
        requiredMark="optional"
      >
        {entity.fields?.map((field) => (
          <Form.Item
            key={field.id || field.name}
            name={field.name}
            label={
              <span>
                {field.displayName}
                {field.unique && (
                  <span style={{ color: '#faad14', marginLeft: 4, fontSize: 12 }}>
                    (唯一)
                  </span>
                )}
              </span>
            }
            rules={getFieldRules(field)}
            valuePropName={field.type === 'boolean' ? 'checked' : 'value'}
            tooltip={field.description}
          >
            {getFieldControl(field)}
          </Form.Item>
        ))}
      </Form>
    </Modal>
  );
};

export default DynamicRecordForm;
