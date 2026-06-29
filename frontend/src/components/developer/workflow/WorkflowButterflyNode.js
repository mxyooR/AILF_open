import { Node } from 'butterfly-dag';

class WorkflowButterflyNode extends Node {
  constructor(opts) {
    super(opts);
    this.options = opts;
  }

  draw = (opts) => {
    // 创建节点容器
    const container = document.createElement('div');
    container.className = 'workflow-butterfly-node';
    container.style.position = 'absolute';
    container.style.left = opts.left + 'px';
    container.style.top = opts.top + 'px';
    container.id = opts.id;

    // 根据节点类型设置样式和图标
    const nodeType = opts.options.nodeType || 'start';
    const nodeConfig = this.getNodeConfig(nodeType);

    // 根据形状类型绘制不同样式的节点
    switch (nodeConfig.shape) {
      case 'diamond':
        return this.drawConditionNode(container, opts, nodeConfig);
      case 'circle':
        return this.drawCircleNode(container, opts, nodeConfig);
      case 'hexagon':
        return this.drawHexagonNode(container, opts, nodeConfig);
      case 'rounded-rect':
      default:
        return this.drawRoundedRectNode(container, opts, nodeConfig);
    }
  }

  // 绘制圆角矩形节点（默认样式）
  drawRoundedRectNode = (container, opts, nodeConfig) => {
    container.style.backgroundColor = nodeConfig.backgroundColor;
    container.style.border = `2px solid ${nodeConfig.borderColor}`;
    container.style.borderRadius = '8px';
    container.style.padding = '12px';
    container.style.minWidth = '120px';
    container.style.textAlign = 'center';
    container.style.cursor = 'pointer';
    container.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';

    // 创建图标
    const icon = document.createElement('div');
    icon.className = 'node-icon';
    icon.innerHTML = nodeConfig.icon;
    icon.style.fontSize = '24px';
    icon.style.marginBottom = '8px';
    icon.style.color = nodeConfig.iconColor;

    // 创建标签
    const label = document.createElement('div');
    label.className = 'node-label';
    label.textContent = opts.options.label || opts.options.name || opts.options.nodeType;
    label.style.fontSize = '12px';
    label.style.fontWeight = '500';
    label.style.color = '#333';
    label.style.wordBreak = 'break-word';

    // 创建删除按钮
    const deleteBtn = this.createDeleteButton(opts.id);

    container.appendChild(icon);
    container.appendChild(label);
    container.appendChild(deleteBtn);

    // 添加事件监听器
    this.addEventListeners(container, deleteBtn, opts);

    return container;
  }

  // 绘制圆形节点
  drawCircleNode = (container, opts, nodeConfig) => {
    container.style.width = '100px';
    container.style.height = '100px';
    container.style.backgroundColor = nodeConfig.backgroundColor;
    container.style.border = `3px solid ${nodeConfig.borderColor}`;
    container.style.borderRadius = '50%';
    container.style.display = 'flex';
    container.style.flexDirection = 'column';
    container.style.alignItems = 'center';
    container.style.justifyContent = 'center';
    container.style.cursor = 'pointer';
    container.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';

    // 创建图标
    const icon = document.createElement('div');
    icon.className = 'node-icon';
    icon.innerHTML = nodeConfig.icon;
    icon.style.fontSize = '28px';
    icon.style.marginBottom = '4px';
    icon.style.color = nodeConfig.iconColor;

    // 创建标签
    const label = document.createElement('div');
    label.className = 'node-label';
    label.textContent = opts.options.label || opts.options.name || opts.options.nodeType;
    label.style.fontSize = '10px';
    label.style.fontWeight = '600';
    label.style.color = '#333';
    label.style.textAlign = 'center';
    label.style.wordBreak = 'break-word';

    // 创建删除按钮
    const deleteBtn = this.createDeleteButton(opts.id);

    container.appendChild(icon);
    container.appendChild(label);
    container.appendChild(deleteBtn);

    // 添加事件监听器
    this.addEventListeners(container, deleteBtn, opts);

    return container;
  }

  // 绘制六边形节点
  drawHexagonNode = (container, opts, nodeConfig) => {
    container.style.width = '140px';
    container.style.height = '80px';
    container.style.backgroundColor = 'transparent';
    container.style.border = 'none';
    container.style.cursor = 'pointer';
    container.style.display = 'flex';
    container.style.alignItems = 'center';
    container.style.justifyContent = 'center';

    // 创建六边形背景
    const hexagon = document.createElement('div');
    hexagon.className = 'hexagon-shape';
    hexagon.style.width = '120px';
    hexagon.style.height = '70px';
    hexagon.style.backgroundColor = nodeConfig.backgroundColor;
    hexagon.style.border = `2px solid ${nodeConfig.borderColor}`;
    hexagon.style.position = 'absolute';
    hexagon.style.clipPath = 'polygon(20% 0%, 80% 0%, 100% 50%, 80% 100%, 20% 100%, 0% 50%)';
    hexagon.style.boxShadow = '0 3px 10px rgba(0,0,0,0.12)';

    // 创建内容容器
    const content = document.createElement('div');
    content.className = 'hexagon-content';
    content.style.position = 'relative';
    content.style.zIndex = '2';
    content.style.textAlign = 'center';
    content.style.display = 'flex';
    content.style.flexDirection = 'column';
    content.style.alignItems = 'center';
    content.style.justifyContent = 'center';

    // 创建图标
    const icon = document.createElement('div');
    icon.className = 'node-icon';
    icon.innerHTML = nodeConfig.icon;
    icon.style.fontSize = '22px';
    icon.style.marginBottom = '4px';
    icon.style.color = nodeConfig.iconColor;

    // 创建标签
    const label = document.createElement('div');
    label.className = 'node-label';
    label.textContent = opts.options.label || opts.options.name || opts.options.nodeType;
    label.style.fontSize = '11px';
    label.style.fontWeight = '500';
    label.style.color = '#333';
    label.style.wordBreak = 'break-word';

    // 创建删除按钮
    const deleteBtn = this.createDeleteButton(opts.id);

    // 组装元素
    content.appendChild(icon);
    content.appendChild(label);

    container.appendChild(hexagon);
    container.appendChild(content);
    container.appendChild(deleteBtn);

    // 添加事件监听器
    this.addEventListeners(container, deleteBtn, opts, hexagon);

    return container;
  }

  // 绘制条件节点（菱形样式）
  drawConditionNode = (container, opts, nodeConfig) => {
    // 设置菱形容器样式
    container.style.width = '140px';
    container.style.height = '80px';
    container.style.backgroundColor = 'transparent';
    container.style.border = 'none';
    container.style.cursor = 'pointer';
    container.style.display = 'flex';
    container.style.alignItems = 'center';
    container.style.justifyContent = 'center';

    // 创建菱形背景
    const diamond = document.createElement('div');
    diamond.className = 'condition-diamond';
    diamond.style.width = '80px';
    diamond.style.height = '80px';
    diamond.style.backgroundColor = nodeConfig.backgroundColor;
    diamond.style.border = `2px solid ${nodeConfig.borderColor}`;
    diamond.style.transform = 'rotate(45deg)';
    diamond.style.position = 'absolute';
    diamond.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';

    // 创建内容容器（不旋转）
    const content = document.createElement('div');
    content.className = 'condition-content';
    content.style.position = 'relative';
    content.style.zIndex = '2';
    content.style.textAlign = 'center';
    content.style.transform = 'rotate(0deg)';

    // 创建图标
    const icon = document.createElement('div');
    icon.className = 'node-icon';
    icon.innerHTML = nodeConfig.icon;
    icon.style.fontSize = '20px';
    icon.style.marginBottom = '4px';
    icon.style.color = nodeConfig.iconColor;

    // 创建标签
    const label = document.createElement('div');
    label.className = 'node-label';
    label.textContent = opts.options.label || opts.options.name || '条件';
    label.style.fontSize = '10px';
    label.style.fontWeight = '500';
    label.style.color = '#333';
    label.style.wordBreak = 'break-word';

    // 创建分支标签
    const yesLabel = document.createElement('div');
    yesLabel.className = 'branch-label yes-label';
    yesLabel.textContent = '是';
    yesLabel.style.position = 'absolute';
    yesLabel.style.right = '-20px';
    yesLabel.style.top = '50%';
    yesLabel.style.transform = 'translateY(-50%)';
    yesLabel.style.fontSize = '10px';
    yesLabel.style.color = '#52c41a';
    yesLabel.style.fontWeight = 'bold';
    yesLabel.style.backgroundColor = 'white';
    yesLabel.style.padding = '2px 4px';
    yesLabel.style.borderRadius = '4px';
    yesLabel.style.border = '1px solid #52c41a';

    const noLabel = document.createElement('div');
    noLabel.className = 'branch-label no-label';
    noLabel.textContent = '否';
    noLabel.style.position = 'absolute';
    noLabel.style.bottom = '-20px';
    noLabel.style.left = '50%';
    noLabel.style.transform = 'translateX(-50%)';
    noLabel.style.fontSize = '10px';
    noLabel.style.color = '#ff4d4f';
    noLabel.style.fontWeight = 'bold';
    noLabel.style.backgroundColor = 'white';
    noLabel.style.padding = '2px 4px';
    noLabel.style.borderRadius = '4px';
    noLabel.style.border = '1px solid #ff4d4f';

    // 创建删除按钮
    const deleteBtn = document.createElement('div');
    deleteBtn.className = 'node-delete-btn';
    deleteBtn.innerHTML = '×';
    deleteBtn.style.position = 'absolute';
    deleteBtn.style.top = '-8px';
    deleteBtn.style.right = '-8px';
    deleteBtn.style.width = '16px';
    deleteBtn.style.height = '16px';
    deleteBtn.style.backgroundColor = '#ff4d4f';
    deleteBtn.style.color = 'white';
    deleteBtn.style.borderRadius = '50%';
    deleteBtn.style.display = 'none';
    deleteBtn.style.alignItems = 'center';
    deleteBtn.style.justifyContent = 'center';
    deleteBtn.style.cursor = 'pointer';
    deleteBtn.style.fontSize = '12px';
    deleteBtn.style.fontWeight = 'bold';
    deleteBtn.style.zIndex = '1000';

    // 删除按钮点击事件
    deleteBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (window.confirm('确定要删除这个节点吗？')) {
        const deleteEvent = new CustomEvent('node-delete', {
          detail: { nodeId: opts.id }
        });
        document.dispatchEvent(deleteEvent);
      }
    });

    // 组装元素
    content.appendChild(icon);
    content.appendChild(label);

    container.appendChild(diamond);
    container.appendChild(content);
    container.appendChild(yesLabel);
    container.appendChild(noLabel);
    container.appendChild(deleteBtn);

    // 添加双击事件
    container.addEventListener('dblclick', (e) => {
      e.stopPropagation();
      const editEvent = new CustomEvent('node-edit', {
        detail: { nodeId: opts.id, nodeType: opts.options.nodeType }
      });
      document.dispatchEvent(editEvent);
    });

    // 添加悬停效果
    container.addEventListener('mouseenter', () => {
      diamond.style.transform = 'rotate(45deg) scale(1.05)';
      diamond.style.transition = 'transform 0.2s ease';
      deleteBtn.style.display = 'flex';
    });

    container.addEventListener('mouseleave', () => {
      diamond.style.transform = 'rotate(45deg) scale(1)';
      deleteBtn.style.display = 'none';
    });

    return container;
  }

  // 创建删除按钮
  createDeleteButton = (nodeId) => {
    const deleteBtn = document.createElement('div');
    deleteBtn.className = 'node-delete-btn';
    deleteBtn.innerHTML = '×';
    deleteBtn.style.position = 'absolute';
    deleteBtn.style.top = '-8px';
    deleteBtn.style.right = '-8px';
    deleteBtn.style.width = '16px';
    deleteBtn.style.height = '16px';
    deleteBtn.style.backgroundColor = '#ff4d4f';
    deleteBtn.style.color = 'white';
    deleteBtn.style.borderRadius = '50%';
    deleteBtn.style.display = 'none';
    deleteBtn.style.alignItems = 'center';
    deleteBtn.style.justifyContent = 'center';
    deleteBtn.style.cursor = 'pointer';
    deleteBtn.style.fontSize = '12px';
    deleteBtn.style.fontWeight = 'bold';
    deleteBtn.style.zIndex = '1000';

    // 删除按钮点击事件
    deleteBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (window.confirm('确定要删除这个节点吗？')) {
        const deleteEvent = new CustomEvent('node-delete', {
          detail: { nodeId: nodeId }
        });
        document.dispatchEvent(deleteEvent);
      }
    });

    return deleteBtn;
  }

  // 添加事件监听器
  addEventListeners = (container, deleteBtn, opts, shapeElement = null) => {
    // 添加双击事件
    container.addEventListener('dblclick', (e) => {
      e.stopPropagation();
      const editEvent = new CustomEvent('node-edit', {
        detail: { nodeId: opts.id, nodeType: opts.options.nodeType }
      });
      document.dispatchEvent(editEvent);
    });

    // 添加悬停效果
    container.addEventListener('mouseenter', () => {
      if (shapeElement) {
        shapeElement.style.transform = shapeElement.style.transform.includes('rotate')
          ? shapeElement.style.transform + ' scale(1.05)'
          : 'scale(1.05)';
        shapeElement.style.transition = 'transform 0.2s ease';
      } else {
        container.style.transform = 'scale(1.05)';
        container.style.transition = 'transform 0.2s ease';
      }
      deleteBtn.style.display = 'flex';
    });

    container.addEventListener('mouseleave', () => {
      if (shapeElement) {
        shapeElement.style.transform = shapeElement.style.transform.replace(' scale(1.05)', '');
      } else {
        container.style.transform = 'scale(1)';
      }
      deleteBtn.style.display = 'none';
    });
  }

  getNodeConfig(nodeType) {
    const configs = {
      start: {
        icon: '▶️',
        backgroundColor: '#e8f5e8',
        borderColor: '#52c41a',
        iconColor: '#52c41a',
        shape: 'circle' // 圆形
      },
      api_call: {
        icon: '🔗',
        backgroundColor: '#e6f7ff',
        borderColor: '#1890ff',
        iconColor: '#1890ff',
        shape: 'hexagon' // 六边形
      },
      api: {
        icon: '🔗',
        backgroundColor: '#e6f7ff',
        borderColor: '#1890ff',
        iconColor: '#1890ff',
        shape: 'hexagon' // 六边形
      },
      user_input: {
        icon: '📝',
        backgroundColor: '#f9f0ff',
        borderColor: '#722ed1',
        iconColor: '#722ed1',
        shape: 'rounded-rect' // 圆角矩形
      },
      input: {
        icon: '📝',
        backgroundColor: '#f9f0ff',
        borderColor: '#722ed1',
        iconColor: '#722ed1',
        shape: 'rounded-rect' // 圆角矩形
      },
      condition: {
        icon: '❓',
        backgroundColor: '#fff7e6',
        borderColor: '#fa8c16',
        iconColor: '#fa8c16',
        shape: 'diamond' // 菱形
      },
      notification: {
        icon: '📢',
        backgroundColor: '#fff0f6',
        borderColor: '#eb2f96',
        iconColor: '#eb2f96',
        shape: 'rounded-rect' // 圆角矩形
      },
      end: {
        icon: '⏹️',
        backgroundColor: '#fff2f0',
        borderColor: '#ff4d4f',
        iconColor: '#ff4d4f',
        shape: 'circle' // 圆形
      }
    };

    return configs[nodeType] || configs.start;
  }
}

export default WorkflowButterflyNode;
