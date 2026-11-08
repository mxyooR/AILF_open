import dayjs from 'dayjs';
import { recordToFormValues, formValuesToRecord } from './recordFormValues';

const field = (name, type, extra = {}) => ({ name, type, ...extra });
test('calendar dates and local departure times survive a round trip without UTC conversion', () => {
  const fields = [field('travel', 'date'), field('departure', 'datetime')];
  const values = recordToFormValues({ travel: '2026-11-08', departure: '2026-11-08 00:30:00' }, fields);
  expect(formValuesToRecord(values, fields)).toEqual({ travel: '2026-11-08', departure: '2026-11-08 00:30:00' });
  expect(formValuesToRecord({ travel: dayjs('2026-11-08') }, fields).travel).toBe('2026-11-08');
});
test('cleared optional fields are submitted as null and do not regain defaults', () => {
  const fields = [field('note', 'text', { defaultValue: '默认内容' }), field('travel', 'date')];
  expect(recordToFormValues({ note: null, travel: null }, fields)).toEqual({ note: null, travel: null });
  expect(formValuesToRecord({ note: null, travel: null }, fields)).toEqual({ note: null, travel: null });
});
test('new record defaults preserve false and zero and convert date defaults to picker values', () => {
  const fields = [field('enabled', 'boolean', { defaultValue: false }), field('count', 'number', { defaultValue: 0 }), field('date', 'date', { defaultValue: '2026-11-08' })];
  const values = recordToFormValues(null, fields);
  expect(values.date.isValid()).toBe(true);
  expect(formValuesToRecord(values, fields)).toEqual({ enabled: false, count: 0, date: '2026-11-08' });
});
test('string false is displayed as an unchecked boolean rather than true', () => {
  expect(recordToFormValues({ enabled: 'false' }, [field('enabled', 'boolean')])).toEqual({ enabled: false });
});
test('JSON fields round trip objects and reject malformed text before submission', () => {
  const fields = [field('settings', 'json')];
  const values = recordToFormValues({ settings: { retries: 0, enabled: false } }, fields);
  expect(formValuesToRecord(values, fields)).toEqual({ settings: { retries: 0, enabled: false } });
  expect(() => formValuesToRecord({ settings: '{bad' }, fields)).toThrow();
});
