import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { JsonForms } from '@jsonforms/react';
import { createAjv } from '@jsonforms/core';
import { vanillaCells, vanillaRenderers } from '@jsonforms/vanilla-renderers';

const ajv = createAjv({ useDefaults: false });
const ui = {
  type: 'VerticalLayout',
  elements: [
    { type: 'Control', scope: '#/properties/id', label: '单元 ID' },
    { type: 'Control', scope: '#/properties/paths', label: '可写路径' },
    { type: 'Control', scope: '#/properties/instructions', label: '任务说明', options: { multi: true } },
  ],
};

export function schemaForm(container) {
  const root = createRoot(container);
  function Editor({ unit, schema, onCommit }) {
    const [data, setData] = useState(() => structuredClone(unit));
    useEffect(() => setData(structuredClone(unit)), [unit]);
    // Runtime Ajv compilation violates the app's CSP. The existing server owns validation.
    return <div className="jsonforms">
      <p className="hint">Schema 生成字段；输入由服务端显式校验。</p>
      <JsonForms validationMode="NoValidation" schema={schema} uischema={ui} data={data} ajv={ajv}
        renderers={vanillaRenderers} cells={vanillaCells} onChange={({ data }) => setData(data)} />
      <button type="button" onClick={() => onCommit(data)}>更新节点</button>
    </div>;
  }
  return {
    update(unit, schema, onCommit) { root.render(<Editor unit={unit} schema={schema} onCommit={onCommit} />); },
    destroy() { root.unmount(); },
  };
}
