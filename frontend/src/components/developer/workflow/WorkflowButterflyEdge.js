import { Edge } from 'butterfly-dag';

class WorkflowButterflyEdge extends Edge {
  constructor(opts) {
    super(opts);
    this.options = opts;
  }

  _dispatchEdgeEvent(eventName) {
    const edgeEvent = new CustomEvent(eventName, {
      detail: {
        edgeId: this.id,
        sourceNode: this.options?.sourceNode,
        targetNode: this.options?.targetNode
      }
    });
    document.dispatchEvent(edgeEvent);
  }

  draw(obj) {
    // 调用父类的draw方法获取基础路径
    let path = super.draw(obj);

    // 设置连线样式
    if (path) {
      path.style.stroke = '#1890ff';
      path.style.strokeWidth = '2px';
      path.style.fill = 'none';
      path.style.cursor = 'pointer';

      // 添加悬停效果
      path.addEventListener('mouseenter', () => {
        path.style.stroke = '#40a9ff';
        path.style.strokeWidth = '3px';
      });

      path.addEventListener('mouseleave', () => {
        path.style.stroke = '#1890ff';
        path.style.strokeWidth = '2px';
      });

      // 添加双击删除事件
      path.addEventListener('dblclick', (e) => {
        e.stopPropagation();
        if (window.confirm('确定要删除这条连线吗？')) {
          this._dispatchEdgeEvent('edge-delete');
        }
      });
    }

    return path;
  }

  drawArrow(isShow) {
    // 调用父类的drawArrow方法
    let arrow = super.drawArrow(isShow);
    
    // 设置箭头样式
    if (arrow && isShow) {
      arrow.style.fill = '#1890ff';
      arrow.style.stroke = '#1890ff';
    }
    
    return arrow;
  }

  drawLabel(text) {
    // 如果有标签文本，创建标签元素
    if (text) {
      const label = document.createElement('div');
      label.className = 'edge-label';
      label.textContent = text;
      label.style.position = 'absolute';
      label.style.backgroundColor = '#fff';
      label.style.border = '1px solid #d9d9d9';
      label.style.borderRadius = '4px';
      label.style.padding = '2px 6px';
      label.style.fontSize = '12px';
      label.style.color = '#666';
      label.style.pointerEvents = 'auto';
      label.style.cursor = 'pointer';
      label.style.zIndex = '1000';

      // 单击标签直接打开连线条件编辑器，避免必须精确点中细线。
      label.addEventListener('click', (e) => {
        e.stopPropagation();
        this._dispatchEdgeEvent('edge-click');
      });

      // 双击标签快速删除连线。
      label.addEventListener('dblclick', (e) => {
        e.stopPropagation();
        if (window.confirm('确定要删除这条连线吗？')) {
          this._dispatchEdgeEvent('edge-delete');
        }
      });
      
      return label;
    }
    
    return null;
  }
}

export default WorkflowButterflyEdge;
