import dayjs from 'dayjs';
import type { EntityDataRecord, EntityField } from '../../../types/developer/entity';

/** 日期字段表示日历日期；不能转 UTC，否则北京时间零点会被保存成前一天。 */
export function recordToFormValues(record: EntityDataRecord | null | undefined, fields: EntityField[]) {
  const values: Record<string, any> = {};
  fields.forEach(field => {
    const value = record ? record[field.name] : field.defaultValue;
    if (field.type === 'date' || field.type === 'datetime') {
      values[field.name] = value != null && dayjs(value).isValid() ? dayjs(value) : null;
    } else if (field.type === 'json' && value != null && typeof value !== 'string') {
      values[field.name] = JSON.stringify(value, null, 2);
    } else if (field.type === 'boolean') {
      values[field.name] = value === true || value === 1 || value === 'true' || value === '1';
    } else {
      // 编辑时保留 null，不能偷偷用默认值覆盖用户已经清空的字段。
      values[field.name] = value;
    }
  });
  return values;
}

export function formValuesToRecord(values: Record<string, any>, fields: EntityField[]) {
  const data: Record<string, any> = {};
  fields.forEach(field => {
    const value = values[field.name];
    if (value === undefined) return;
    if (value === null) {
      data[field.name] = null;
    } else if (field.type === 'date' || field.type === 'datetime') {
      // 数据库的 date/datetime 无时区，按用户选择的本地日期和时间提交。
      data[field.name] = dayjs(value).format(field.type === 'date' ? 'YYYY-MM-DD' : 'YYYY-MM-DD HH:mm:ss');
    } else if (field.type === 'json' && typeof value === 'string') {
      data[field.name] = value.trim() ? JSON.parse(value) : null;
    } else {
      data[field.name] = value;
    }
  });
  return data;
}
