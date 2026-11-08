import { Node } from 'butterfly-dag';

const styles = {
  start: { caption: '开始', color: '#3e8b65', background: '#eef8f1', path: '<path d="m9 5 10 7-10 7z" />' },
  api_call: { caption: 'API CALL', color: '#3685c4', background: '#edf6fd', path: '<path d="m8 8-5 4 5 4m8-8 5 4-5 4m-3-10-2 12" />' },
  condition: { caption: 'CONDITION', color: '#cf922b', background: '#fff8e9', path: '<path d="M7 3v5a4 4 0 0 0 4 4h6M7 12v9m10-13 4 4-4 4" />' },
  notification: { caption: 'NOTIFICATION', color: '#b96191', background: '#fcf0f7', path: '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9m-9 13h6" />' },
  end: { caption: '结束', color: '#c36c69', background: '#fdf1f0', path: '<rect x="6" y="6" width="12" height="12" rx="2" />' }
};

class WorkflowButterflyNode extends Node {
  draw = (options) => {
    // Butterfly wraps the node definition in draw.options.
    const data = options.options?.options || options.options || {};
    const type = data.nodeType || 'start';
    const style = styles[type] || styles.start;
    const name = data.label || data.name || type;
    const container = document.createElement('div');
    container.className = `workflow-butterfly-node is-${type}`;
    container.id = options.id;
    container.dataset.nodeType = type;
    container.style.left = `${options.left}px`;
    container.style.top = `${options.top}px`;
    container.style.setProperty('--node-color', style.color);
    container.style.setProperty('--node-background', style.background);
    container.setAttribute('role', 'button');
    container.setAttribute('aria-label', `${name}，${style.caption}节点`);
    container.tabIndex = 0;

    const shape = document.createElement('div');
    shape.className = 'workflow-node-shape';
    const content = document.createElement('div');
    content.className = 'workflow-node-content';
    const icon = document.createElement('div');
    icon.className = 'workflow-node-symbol';
    icon.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${style.path}</svg>`;
    const label = document.createElement('div');
    label.className = 'node-label';
    label.textContent = name;
    const caption = document.createElement('small');
    caption.className = 'workflow-node-caption';
    caption.textContent = style.caption;
    content.append(icon, label, caption);

    const dispatch = type => container.dispatchEvent(new CustomEvent(type, { bubbles: true, detail: { nodeId: options.id, nodeType: data.nodeType } }));
    const editable = () => !container.closest('.workflow-canvas.readonly');
    container.addEventListener('dblclick', event => { event.stopPropagation(); if (editable()) dispatch('node-edit'); });
    container.addEventListener('keydown', event => {
      if (event.target === container && (event.key === 'Enter' || event.key === ' ')) {
        event.preventDefault(); if (editable()) dispatch('node-edit');
      }
    });
    const remove = document.createElement('button');
    remove.type = 'button'; remove.className = 'node-delete-btn'; remove.textContent = '×';
    remove.setAttribute('aria-label', `删除节点：${name}`);
    remove.addEventListener('mousedown', event => event.stopPropagation());
    remove.addEventListener('click', event => {
      event.stopPropagation();
      if (editable() && window.confirm('确定要删除这个节点及其关联连线吗？')) dispatch('node-delete');
    });
    container.append(shape, content, remove);
    return container;
  }
}

export default WorkflowButterflyNode;
