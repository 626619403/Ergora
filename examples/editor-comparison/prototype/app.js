import './style.css';
import { api } from '@ergora/api';

function element(tag, text, attributes = {}) {
  const node = document.createElement(tag);
  if (text !== null) node.textContent = text;
  for (const [name, value] of Object.entries(attributes)) node.setAttribute(name, value);
  return node;
}

function select(label, items, value) {
  const wrapper = element('label', label);
  const input = element('select', null, { 'aria-label': label });
  for (const item of items) {
    const option = element('option', item, { value: item });
    option.selected = item === value;
    input.append(option);
  }
  wrapper.append(input);
  return { wrapper, input };
}

export function nativeForm(container) {
  return {
    update(unit, schema, onCommit) {
      container.replaceChildren();
      const form = element('form', null);
      const fields = {};
      const definitions = [
        ['id', '单元 ID', false],
        ['paths', '可写路径', true],
        ['instructions', '任务说明', true],
      ];
      for (const [key, label, multiline] of definitions) {
        const wrapper = element('label', label);
        const input = element(multiline ? 'textarea' : 'input', null, {
          'aria-label': label, required: '',
        });
        input.value = key === 'paths' ? unit.paths.join('\n') : unit[key];
        fields[key] = input;
        wrapper.append(input);
        form.append(wrapper);
      }
      form.append(element('button', '更新节点', { type: 'submit' }));
      form.addEventListener('submit', event => {
        event.preventDefault();
        onCommit({
          ...unit,
          id: fields.id.value.trim(),
          paths: fields.paths.value.split('\n').map(value => value.trim()).filter(Boolean),
          instructions: fields.instructions.value,
        });
      });
      container.append(form);
    },
    destroy() { container.replaceChildren(); },
  };
}

export async function start(adapter) {
  const app = document.querySelector('#app');
  const project = new URLSearchParams(location.search).get('project');
  const status = element('div', '', { role: 'status', class: 'status' });
  const show = (message, error = false) => {
    status.textContent = message;
    status.classList.toggle('error', error);
  };
  app.replaceChildren(
    element('h1', '编辑器比较 · ' + adapter.title),
    element('p', '试验草稿只使用两个开发模板；校验和保存沿用本地合同接口。'),
    status,
  );
  if (!project) {
    show('请在地址中提供 ?project=已建立的试验项目 ID。', true);
    return;
  }

  try {
    const nav = element('nav', null);
    for (const mode of ['native', 'flow', 'schema']) {
      nav.append(element('a', mode, {
        href: mode + '.html?project=' + encodeURIComponent(project),
      }));
    }
    app.append(nav);
    const schemas = await api('schemas.json');
    const data = await api('/api/projects/' + encodeURIComponent(project) + '/dashboard');
    const revisions = new Map(data.drafts.map(draft => [draft.id, draft.revision]));
    const choice = select('开发模板', ['repository-governance', 'large-change'], 'repository-governance');
    app.append(choice.wrapper);

    const layout = element('div', null, { class: 'layout' });
    const left = element('section', null);
    const right = element('section', null);
    const canvas = element('div', null, { class: 'graph', 'aria-label': '工作单元图' });
    const graphHint = adapter.name === 'flow'
      ? '从节点端口拖动连线；下方表单也可编辑依赖。'
      : '按住 Shift 点起点，再点终点连接；下方表单也可编辑依赖。';
    left.append(element('h2', '工作单元与依赖'), canvas, element('p', graphHint, { class: 'hint' }));
    const selection = select('当前单元', [], null);
    const properties = element('div', null);
    right.append(selection.wrapper, properties);
    layout.append(left, right);
    app.append(layout);
    const edges = element('div', null, { class: 'toolbar' });
    left.append(edges);
    const controls = element('div', null, { class: 'toolbar' });
    const validation = element('pre', '尚未校验', { id: 'validation' });
    app.append(controls, validation);
    const jsonSection = element('section', null, { class: 'wide' });
    const json = element('textarea', null, { class: 'json', 'aria-label': '完整输入 JSON' });
    jsonSection.append(element('h2', '同一份语义输入'), json);
    app.append(jsonSection);

    let input = null;
    let selected = null;
    let kind = choice.input.value;
    let epoch = 0;
    const form = adapter.form(properties);
    const graph = adapter.graph(canvas, id => {
      selected = id;
      renderSelection();
    }, (source, target) => change(() => {
      const unit = input.work_units.find(unit => unit.id === target);
      if (!unit.depends_on.includes(source)) unit.depends_on.push(source);
    }));
    const draftId = () => 'editor-' + adapter.name + '-' + kind;
    const payload = () => ({
      id: draftId(), kind, input: structuredClone(input), revision: revisions.get(draftId()) || 0,
    });
    const projectApi = '/api/projects/' + encodeURIComponent(project);

    function action(parent, label, callback) {
      const button = element('button', label, { type: 'button' });
      button.addEventListener('click', () => {
        Promise.resolve().then(callback).catch(error => show(error.message, true));
      });
      parent.append(button);
      return button;
    }

    function change(update) {
      update();
      epoch++;
      renderSemantic();
      show('本次输入已修改；尚未保存。');
    }

    function commit(unit) {
      const previous = selected;
      // A node needs an identity to project into either graph library.
      if (!unit.id) { show('单元 ID 不能为空', true); return; }
      if (input.work_units.some(other => other.id !== previous && other.id === unit.id)) {
        show('单元 ID 已存在', true);
        return;
      }
      change(() => {
        input.work_units = input.work_units.map(other => {
          const value = other.id === previous ? structuredClone(unit) : other;
          return { ...value, depends_on: value.depends_on.map(id => id === previous ? unit.id : id) };
        });
        selected = unit.id;
      });
    }

    function renderSelection() {
      const current = select('当前单元', input.work_units.map(unit => unit.id), selected);
      selection.wrapper.replaceChildren(document.createTextNode('当前单元'), current.input);
      selection.input = current.input;
      selection.input.addEventListener('change', () => {
        selected = selection.input.value;
        renderSelection();
      });
      form.update(input.work_units.find(unit => unit.id === selected), schemas[kind].properties.work_units.items, commit);
      graph.update(input.work_units, selected);
    }

    function renderSemantic() {
      json.value = JSON.stringify(input, null, 2);
      validation.textContent = '当前输入尚未校验';
      renderSelection();
      edges.replaceChildren();
      const source = select('依赖起点', input.work_units.map(unit => unit.id), input.work_units[0].id);
      const target = select('依赖终点', input.work_units.map(unit => unit.id), input.work_units.at(-1).id);
      edges.append(source.wrapper, target.wrapper);
      action(edges, '添加依赖', () => change(() => {
        const unit = input.work_units.find(unit => unit.id === target.input.value);
        if (!unit.depends_on.includes(source.input.value)) unit.depends_on.push(source.input.value);
      }));
      action(edges, '移除依赖', () => change(() => {
        const unit = input.work_units.find(unit => unit.id === target.input.value);
        unit.depends_on = unit.depends_on.filter(id => id !== source.input.value);
      }));
    }

    async function load() {
      const request = ++epoch;
      const requestedKind = choice.input.value;
      const template = await api('/api/templates/' + requestedKind);
      if (request !== epoch) return;
      kind = requestedKind;
      input = structuredClone(template.input);
      selected = input.work_units[0].id;
      renderSemantic();
      show('已载入模板，未保存试验草稿。');
    }

    choice.input.addEventListener('change', () => load().catch(error => show(error.message, true)));
    action(controls, '校验当前输入', async () => {
      const request = epoch;
      const result = await api(projectApi + '/drafts/validate', payload());
      if (request !== epoch) return;
      validation.textContent = JSON.stringify(result, null, 2);
      show('当前合同校验通过；没有执行任务。');
    });
    action(controls, '保存试验草稿', async () => {
      const request = epoch;
      const result = await api(projectApi + '/drafts', payload());
      revisions.set(result.id, result.revision);
      show(request === epoch ? '草稿已保存 r' + result.revision : '先前快照已保存；当前编辑仍未保存。');
    });
    action(jsonSection, '校验并载入 JSON', async () => {
      const next = JSON.parse(json.value);
      const request = epoch;
      await api(projectApi + '/drafts/validate', { ...payload(), input: next });
      if (request !== epoch) return;
      change(() => { input = next; selected = input.work_units[0].id; });
    });
    window.addEventListener('pagehide', () => { graph.destroy(); form.destroy(); }, { once: true });
    await load();
  } catch (error) { show(error.message, true); }
}
