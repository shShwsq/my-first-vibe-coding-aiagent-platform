<template>
  <div class="chat-container">
    <div class="main-content" :class="{ 'sidebar-open': showHistory, 'test-progress-open': showTestProgress && chatMode === 'test' }">
      <button class="history-toggle" 
              @click="handleHistoryToggle" 
              @mousedown="startHistoryDrag"
              :title="showHistory ? '关闭历史' : '查看历史'"
              :style="{ top: historyButtonPosition + '%' }">
        <svg viewBox="0 0 24 24">
          <path v-if="!showHistory" fill="currentColor" d="M15.41,16.58L10.83,12L15.41,7.41L14,6L8,12L14,18L15.41,16.58Z"/>
          <path v-else fill="currentColor" d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z"/>
        </svg>
      </button>
      <div class="messages-area" ref="messagesArea" @scroll="onMessagesScroll">
        <div class="messages-wrapper">
          <div v-if="messages.length === 0" class="empty-state">
            <div class="empty-icon">
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M12 3C17.5 3 22 6.58 22 11C22 15.42 17.5 19 12 19C10.76 19 9.57 18.82 8.47 18.5C5.55 21 2 21 2 21C4.33 18.67 4.7 17.1 4.75 16.5C3.05 15.07 2 13.13 2 11C2 6.58 6.5 3 12 3M12 5C7.58 5 4 7.69 4 11C4 12.63 4.95 14.17 6.5 15.25L7.13 15.72L7.08 16.5C7.04 17.04 6.87 17.71 6.5 18.5C7.5 18.25 8.5 17.83 9.5 17.25L10.05 16.93L10.67 17.05C11.38 17.19 12.17 17.25 12.97 17.19C13 17.19 13 17.19 13 17.19C17.42 17.19 21 14.5 21 11.19C21 7.88 17.42 5.19 13 5.19C12.67 5.19 12.33 5.21 12 5.24V5Z"/>
              </svg>
            </div>
            <h3>开始对话</h3>
            <p>在上方选择模型，然后在下方输入问题开始对话</p>
          </div>
          
          <div v-for="(message, index) in messages" :key="index" 
               class="message" 
               :class="[
                 message.role === 'reasoning' ? 'assistant reasoning-message' : message.role,
                 (message.role !== 'user' && index > 0 && messages[index - 1].role !== 'user') ? 'no-avatar' : ''
               ]">
            <div class="message-avatar" v-if="!(message.role !== 'user' && index > 0 && messages[index - 1].role !== 'user')">
              <span v-if="message.role === 'user'">{{ username?.charAt(0).toUpperCase() }}</span>
              <svg v-else viewBox="0 0 24 24">
                <path fill="currentColor" d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4M12,6A6,6 0 0,0 6,12A6,6 0 0,0 12,18A6,6 0 0,0 18,12A6,6 0 0,0 12,6M12,8A4,4 0 0,1 16,12A4,4 0 0,1 12,16A4,4 0 0,1 8,12A4,4 0 0,1 12,8Z"/>
              </svg>
            </div>
            <div class="message-content">
              <div v-if="message.role === 'reasoning'" class="message-reasoning" :class="{ collapsed: message.collapsed }">
                <div class="reasoning-header" @click="message.collapsed = !message.collapsed">
                  <svg viewBox="0 0 24 24" width="14" height="14">
                    <path fill="currentColor" d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4M12,6A6,6 0 0,0 6,12A6,6 0 0,0 12,18A6,6 0 0,0 18,12A6,6 0 0,0 12,6M12,8A4,4 0 0,1 16,12A4,4 0 0,1 12,16A4,4 0 0,1 8,12A4,4 0 0,1 12,8Z"/>
                  </svg>
                  <span>深度思考</span>
                  <svg class="collapse-icon" viewBox="0 0 24 24" width="16" height="16">
                    <path fill="currentColor" d="M7.41,8.58L12,13.17L16.59,8.58L18,10L12,16L6,10L7.41,8.58Z"/>
                  </svg>
                </div>
                <div class="reasoning-content" 
                  v-show="!message.collapsed"
                  :ref="el => { if (el) setReasoningRef(el, index) }"
                  @scroll="onReasoningScroll($event, index)"
                >{{ message.content }}</div>
              </div>
              <div v-else class="message-text">
                <MarkdownRenderer :content="message.content" />
              </div>
              <WorkflowUI 
                v-if="message.ui_config && message.role === 'assistant'" 
                :ui-config="message.ui_config"
                @send-text="handleSendText"
              />
            </div>
          </div>
          
          <div v-if="loading && (messages.length === 0 || (messages[messages.length - 1].role !== 'assistant' && messages[messages.length - 1].role !== 'reasoning') || !messages[messages.length - 1].content)" class="message assistant loading">
            <div class="message-avatar">
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4M12,6A6,6 0 0,0 6,12A6,6 0 0,0 12,18A6,6 0 0,0 18,12A6,6 0 0,0 12,6M12,8A4,4 0 0,1 16,12A4,4 0 0,1 12,16A4,4 0 0,1 8,12A4,4 0 0,1 12,8Z"/>
              </svg>
            </div>
            <div class="message-content">
              <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
          
          <div v-if="chatMode === 'test' && testModeStatus === 'start_testing'" class="test-config-panel">
            <div class="test-config-header">
              <svg viewBox="0 0 24 24" width="20" height="20">
                <path fill="currentColor" d="M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.21,8.95 2.27,9.22 2.46,9.37L4.57,11C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.21,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.67 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z"/>
              </svg>
              <span>测试配置</span>
            </div>
            <div class="test-config-body">
              <div class="config-item">
                <label>选择智能体（可多选）</label>
                <div class="agent-checkboxes">
                  <label v-for="agent in availableAgents" :key="agent.id" class="checkbox-label">
                    <input type="checkbox" :value="agent.name" v-model="selectedAgentNames" />
                    <span>{{ agent.name }}</span>
                  </label>
                </div>
              </div>
              <div class="config-item">
                <label>选择测试用例文件夹</label>
                <select v-model="selectedTestCase" class="test-case-select">
                  <option value="">请选择</option>
                  <option v-for="folder in availableTestFolders" :key="folder.id" :value="folder.name">
                    {{ folder.name }}
                  </option>
                </select>
              </div>
              <div class="config-actions">
                <button class="btn-save-config" @click="saveTestConfig" :disabled="selectedAgentNames.length === 0 || !selectedTestCase">
                  保存配置
                </button>
                <button class="btn-start-test" @click="confirmStartTest" :disabled="selectedAgentNames.length === 0 || !selectedTestCase">
                  确认开始测试
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="input-area">
        <div class="input-wrapper">
          <div v-if="uploadedFiles.length > 0" class="uploaded-files-list">
            <div v-for="(file, index) in uploadedFiles" :key="index" class="uploaded-file-item">
              <svg viewBox="0 0 24 24" class="file-icon">
                <path fill="currentColor" d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
              </svg>
              <span class="file-name">{{ file.name }}</span>
              <span class="file-embedding-status" :class="{
                'processing': file.embedding_status === 'processing',
                'completed': file.embedding_status === 'completed',
                'failed': file.embedding_status === 'failed'
              }">
                <span v-if="file.embedding_status === 'processing'" class="loading-spinner"></span>
                <span v-else-if="file.embedding_status === 'completed'">已解析</span>
                <span v-else-if="file.embedding_status === 'failed'" :title="file.embedding_error">解析失败</span>
                <span v-else>等待中</span>
              </span>
              <button class="remove-file-btn" @click="removeFile(index)" title="移除文件">
                <svg viewBox="0 0 24 24">
                  <path fill="currentColor" d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
                </svg>
              </button>
            </div>
          </div>
          <div class="input-options">
            <button 
              v-if="chatMode !== 'test'"
              class="upload-file-btn"
              @click="triggerFileInput"
              :title="'上传文件'"
            >
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20M12,11L16,15H13.5V18H10.5V15H8L12,11Z"/>
              </svg>
              <span>上传文件</span>
              <span v-if="uploadedFiles.length > 0">({{ uploadedFiles.length }})</span>
            </button>
            <button 
              v-if="chatMode !== 'test'"
              class="upload-file-btn"
              @click="openExistingFilesModal"
              :title="'选择已上传文件'"
            >
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M10,4H4C2.89,4 2,4.89 2,6V18A2,2 0 0,0 4,20H20A2,2 0 0,0 22,18V8C22,6.89 21.1,6 20,6H12L10,4Z"/>
              </svg>
              <span>选择文件</span>
            </button>
            <input 
              type="file" 
              ref="fileInputRef"
              @change="handleFileUpload"
              accept=".pdf,.xlsx,.xls,.docx,.doc,.ppt,.pptx,.png,.jpg,.jpeg,.gif,.webp,.bmp"
              multiple
              style="display: none"
            />
            <button 
              class="thinking-btn" 
              :class="{ active: enableThinking }"
              @click="enableThinking = !enableThinking"
              :title="enableThinking ? '关闭深度思考' : '开启深度思考'"
            >
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M12,2A10,10 0 0,1 22,12A10,10 0 0,1 12,22A10,10 0 0,1 2,12A10,10 0 0,1 12,2M12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20A8,8 0 0,0 20,12A8,8 0 0,0 12,4M12,6A6,6 0 0,1 18,12A6,6 0 0,1 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6M12,8A4,4 0 0,0 8,12A4,4 0 0,0 12,16A4,4 0 0,0 16,12A4,4 0 0,0 12,8Z"/>
              </svg>
              <span>深度思考</span>
            </button>
            <button 
              class="search-btn" 
              :class="{ active: enableSearch }"
              @click="enableSearch = !enableSearch"
              :title="enableSearch ? '关闭联网搜索' : '开启联网搜索'"
            >
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M15.5,12C18,12 20,14 20,16.5C20,17.38 19.75,18.21 19.31,18.9L22.39,22L21,23.39L17.88,20.32C17.19,20.75 16.37,21 15.5,21C13,21 11,19 11,16.5C11,14 13,12 15.5,12M15.5,14A2.5,2.5 0 0,0 13,16.5A2.5,2.5 0 0,0 15.5,19A2.5,2.5 0 0,0 18,16.5A2.5,2.5 0 0,0 15.5,14M10,4A4,4 0 0,1 14,8C14,8.73 13.81,9.41 13.46,10H10V10.54C9.41,10.19 8.73,10 8,10A4,4 0 0,1 4,6A4,4 0 0,1 8,2H16A4,4 0 0,1 20,6A4,4 0 0,1 16,10H13.46C13.81,9.41 14,8.73 14,8A4,4 0 0,0 10,4Z"/>
              </svg>
              <span>联网搜索</span>
            </button>
            <div v-if="chatMode === 'test'" class="interval-input-wrapper">
              <input 
                type="number" 
                v-model.number="requestInterval" 
                class="interval-input"
                min="0"
                placeholder="间隔"
                title="请求时间间隔（秒）"
                @blur="saveRequestInterval"
              />
              <span class="interval-unit">秒</span>
            </div>
            <button 
              v-if="chatMode === 'test'" 
              class="progress-toggle-btn"
              :class="{ active: showTestProgress }"
              @click="showTestProgress = !showTestProgress"
              title="显示进度"
            >
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M13,2.05V3.03C14.28,3.11 15.5,3.45 16.61,4.03L16,5.1C14.5,4.35 12.82,4.05 11.11,4.25C9.39,4.45 7.82,5.2 6.58,6.33C5.33,7.46 4.47,8.92 4.11,10.53C3.75,12.14 3.91,13.83 4.56,15.36C5.21,16.88 6.33,18.17 7.75,19.05C9.17,19.93 10.83,20.36 12.5,20.29C14.17,20.22 15.79,19.65 17.13,18.66C18.47,17.67 19.47,16.3 20,14.75L21.05,15.13C20.38,17.09 19.09,18.79 17.38,19.97C15.68,21.15 13.65,21.75 11.58,21.68C9.5,21.61 7.52,20.87 5.9,19.58C4.29,18.28 3.12,16.5 2.58,14.5C2.04,12.5 2.14,10.38 2.88,8.44C3.62,6.5 4.96,4.84 6.7,3.7C8.44,2.56 10.5,2 12.58,2.05L13,2.05M21.95,12.05C21.95,12.36 21.93,12.66 21.89,12.96L20.89,12.84C20.93,12.58 20.95,12.32 20.95,12.05C20.95,11.78 20.93,11.52 20.89,11.26L21.89,11.14C21.93,11.44 21.95,11.74 21.95,12.05M21.5,9.72L20.56,10.06C20.36,9.53 20.1,9.03 19.78,8.56L20.59,7.97C21,8.55 21.32,9.16 21.5,9.72M19.41,6.83L18.69,7.5C18.31,7.11 17.89,6.77 17.44,6.47L18,5.58C18.56,5.95 19.03,6.38 19.41,6.83M16.47,4.97L16.06,5.91C15.56,5.69 15.03,5.53 14.47,5.44L14.63,4.44C15.3,4.55 15.94,4.73 16.47,4.97Z"/>
              </svg>
              <span>进度</span>
            </button>
            <div v-if="chatMode === 'chat'" class="kb-selector">
              <button class="kb-select-btn" :class="{ active: selectedKB }" @click="toggleKBDropdown">
                <svg viewBox="0 0 24 24" class="kb-icon">
                  <path fill="currentColor" d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20M10,19L12,15H9V10H15V15L13,19H10Z"/>
                </svg>
                <span>{{ selectedKB?.name || '选择知识库' }}</span>
                <svg viewBox="0 0 24 24" class="dropdown-icon">
                  <path fill="currentColor" d="M7.41,8.58L12,13.17L16.59,8.58L18,10L12,16L6,10L7.41,8.58Z"/>
                </svg>
              </button>
              <div v-if="showKBDropdown" class="kb-dropdown">
                <div 
                  class="dropdown-item"
                  :class="{ active: selectedKB === null }"
                  @click="selectKB(null)"
                >
                  <div class="kb-name">不使用知识库</div>
                  <div class="kb-count"></div>
                </div>
                <div 
                  v-for="kb in knowledgeBases" 
                  :key="kb.id" 
                  class="dropdown-item"
                  :class="{ active: selectedKB?.id === kb.id }"
                  @click="selectKB(kb)"
                >
                  <div class="kb-name">{{ kb.name }}</div>
                  <div class="kb-count">{{ kb.file_count || 0 }} 个文件</div>
                </div>
              </div>
            </div>
          </div>
          <div class="input-row">
            <AgentMention
              v-if="chatMode === 'agent' || chatMode === 'test'"
              ref="inputRef"
              v-model="inputMessage"
              :agents="availableAgents"
              :placeholder="chatMode === 'agent' ? '使用 @智能体名称 调用智能体...' : '使用 @智能体名称 和测试用例文件夹进行测试...'"
              @submit="sendMessage"
            />
            <textarea
              v-else
              v-model="inputMessage" 
              @keydown.enter.exact.prevent="sendMessage"
              @input="autoResizeTextarea"
              :placeholder="chatMode === 'chat' ? '输入消息，可选择知识库进行RAG增强...' : '输入消息...'"
              rows="1"
              ref="inputRef"
            ></textarea>
            <button 
              v-if="!loading" 
              class="send-btn" 
              @click="sendMessage" 
              :disabled="!inputMessage.trim() || !selectedModel"
            >
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M2,21L23,12L2,3V10L17,12L2,14V21Z"/>
              </svg>
            </button>
            <button 
              v-else 
              class="stop-btn" 
              @click="stopGeneration"
              title="停止生成"
            >
              <svg viewBox="0 0 24 24">
                <path fill="currentColor" d="M18,18H6V6H18V18Z"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <TestProgressSidebar 
      v-if="chatMode === 'test'"
      :isOpen="showTestProgress" 
      :testProgress="testProgress"
      @close="showTestProgress = false"
    />
    
    <div class="history-sidebar" :class="{ open: showHistory }">
      <div class="sidebar-header">
        <h3>历史对话</h3>
        <button class="new-chat-btn" @click="startNewChat" title="新建对话">
          <svg viewBox="0 0 24 24">
            <path fill="currentColor" d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z"/>
          </svg>
        </button>
      </div>
      
      <div class="history-list" @scroll="onHistoryScroll" ref="historyListRef">
        <div v-if="chatHistory.length === 0 && !historyLoading" class="empty-history">
          <p>暂无历史对话</p>
        </div>
        
        <div 
          v-for="chat in chatHistory" 
          :key="chat.id" 
          class="history-item"
          :class="{ active: currentChatId === chat.id }"
          @click="loadChat(chat)"
        >
          <div class="history-info">
            <div class="history-title">{{ chat.title }}</div>
            <div class="history-meta">
              <span class="history-time">{{ formatTime(chat.updated_at) }}</span>
            </div>
          </div>
          <button class="delete-btn" @click.stop="deleteChat(chat.id)" title="删除">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z"/>
            </svg>
          </button>
        </div>
        
        <div v-if="historyLoading" class="loading-more">
          <span>加载中...</span>
        </div>
        
        <div v-if="hasMoreHistory && !historyLoading" class="load-more" @click="loadMoreHistory">
          <span>加载更多</span>
        </div>
      </div>
    </div>
    
    <div class="toast" v-if="toast.show" :class="toast.type">
      {{ toast.message }}
    </div>

    <div v-if="showExistingFilesModal" class="modal-overlay" @click.self="closeExistingFilesModal">
      <div class="existing-files-modal">
        <div class="modal-header">
          <h3>选择已上传的文件</h3>
          <button class="close-btn" @click="closeExistingFilesModal">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div v-if="loadingExistingFiles" class="loading-state">加载中...</div>
          <div v-else-if="existingFiles.length === 0" class="empty-state">暂无已上传的文件</div>
          <div v-else class="existing-files-list">
            <div 
              v-for="file in existingFiles" 
              :key="file.file_path" 
              class="existing-file-item"
              :class="{ selected: isFileSelected(file.file_path) }"
              @click="toggleExistingFile(file)"
            >
              <svg viewBox="0 0 24 24" class="file-icon">
                <path fill="currentColor" d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
              </svg>
              <span class="file-name" :title="file.filename">{{ file.filename }}</span>
              <span class="file-size">{{ formatFileSize(file.file_size) }}</span>
              <span class="file-type">{{ file.file_type }}</span>
              <span class="file-status" :class="{
                'completed': file.embedding_status === 'completed',
                'processing': file.embedding_status === 'processing',
                'failed': file.embedding_status === 'failed',
                'unknown': file.embedding_status === 'unknown'
              }">
                {{ file.embedding_status === 'completed' ? '已解析' : file.embedding_status === 'processing' ? '解析中' : file.embedding_status === 'failed' ? '失败' : '未知' }}
              </span>
              <svg v-if="isFileSelected(file.file_path)" class="check-icon" viewBox="0 0 24 24">
                <path fill="currentColor" d="M9,20.42L2.79,14.21L5.62,11.38L9,14.77L18.88,4.88L21.71,7.71L9,20.42Z"/>
              </svg>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <span class="selected-count">已选择 {{ selectedExistingFiles.length }} 个文件</span>
          <button class="btn-confirm" @click="confirmExistingFiles" :disabled="selectedExistingFiles.length === 0">
            确认添加
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, computed, inject, provide, onMounted, onActivated, watch, onUnmounted } from 'vue'
import axios from 'axios'
import MarkdownRenderer from '../components/MarkdownRenderer.vue'
import TestProgressSidebar from '../components/TestProgressSidebar.vue'
import AgentMention from '../components/AgentMention.vue'
import WorkflowUI from '../components/WorkflowUI.vue'

const CACHE_KEY = 'chat_history_cache'
const MAX_CACHE = 50
const PAGE_SIZE = 20

const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const messagesArea = ref(null)
const inputRef = ref(null)
const historyListRef = ref(null)
const selectedModel = inject('selectedModel', ref(null))
const chatTitle = inject('chatTitle', ref(''))
const currentChatId = inject('currentChatId', ref(null))
const chatHistory = inject('chatHistory', ref([]))
const chatMode = inject('chatMode', ref('chat'))
const hasMessages = inject('hasMessages', ref(false))
const newChatTrigger = inject('newChatTrigger', ref(0))

watch(messages, (newMessages) => {
  hasMessages.value = newMessages.length > 0
}, { immediate: true, deep: true })

watch(newChatTrigger, () => {
  startNewChat()
})
const toast = ref({ show: false, message: '', type: 'error' })
const enableThinking = ref(false)
const enableSearch = ref(false)
const requestInterval = ref(0)
const abortController = ref(null)
const reasoningRefs = ref({})
const userScrolling = ref({})
const userScrollingMain = ref(false)
const search = ref(false)


const knowledgeBases = ref([])
const selectedKB = ref(null)
const showKBDropdown = ref(false)

const testModeStatus = ref('pending')
const testModeAgentNames = ref([])
const testModeTestCase = ref('')

const showTestProgress = ref(false)
const testProgress = ref({})
let ws = null
let wsReconnectTimer = null

const uploadedFiles = ref([])
const fileInputRef = ref(null)
const uploadingFileKBId = ref(null)
const fileStatusPollingTimers = ref({})

const showExistingFilesModal = ref(false)
const loadingExistingFiles = ref(false)
const existingFiles = ref([])
const selectedExistingFiles = ref([])

const fetchUserInfo = async () => {
  try {
    const response = await axios.get('/api/auth/me')
    localStorage.setItem('userId', response.data.id)
    return response.data.id
  } catch (e) {
    console.error('Failed to fetch user info:', e)
  }
  return null
}

const connectWebSocket = async () => {
  let userId = localStorage.getItem('userId')
  if (!userId) {
    userId = await fetchUserInfo()
    if (!userId) return
  }
  
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${wsProtocol}//${window.location.host}/api/test-chat/ws/${userId}`
  
  ws = new WebSocket(wsUrl)
  
  ws.onopen = () => {
    console.log('WebSocket connected successfully')
    if (wsReconnectTimer) {
      clearTimeout(wsReconnectTimer)
      wsReconnectTimer = null
    }
  }
  
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      handleWebSocketMessage(data)
    } catch (e) {
      console.error('Failed to parse WebSocket message:', e)
    }
  }
  
  ws.onclose = () => {
    console.log('WebSocket disconnected')
    ws = null
    if (!wsReconnectTimer) {
      wsReconnectTimer = setTimeout(() => {
        connectWebSocket()
      }, 3000)
    }
  }
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
  }
}

const handleWebSocketMessage = (data) => {
  if (data.type === 'test_progress') {
    testProgress.value[data.agent_id] = {
      agent_id: data.agent_id,
      agent_name: data.agent_name,
      status: data.status,
      total: data.total,
      current: data.current,
      message: data.message,
      success_count: data.success_count,
      error_count: data.error_count
    }
    
    if (data.status === 'started' || data.status === 'testing') {
      showTestProgress.value = true
    }
    
    if (data.status === 'completed' || data.status === 'error') {
      testModeStatus.value = data.status === 'completed' ? 'completed' : 'error'
    }
  } else if (data.type === 'test_all_started') {
    showTestProgress.value = true
    testProgress.value = {}
  } else if (data.type === 'test_all_completed') {
    testModeStatus.value = 'completed'
    messages.value.push({
      role: 'assistant',
      content: data.message || '测试完成！'
    })
    scrollToBottom()
  } else if (data.type === 'test_all_error') {
    testModeStatus.value = 'error'
    messages.value.push({
      role: 'assistant',
      content: data.message || '测试出错'
    })
    scrollToBottom()
  } else if (data.type === 'test_case_generation_started') {
    showTestProgress.value = true
    testProgress.value['generation'] = {
      agent_id: 'generation',
      agent_name: data.agent_names?.join('、') || '智能体',
      status: 'started',
      message: data.message
    }
  } else if (data.type === 'test_case_generation_progress') {
    testProgress.value['generation'] = {
      agent_id: 'generation',
      agent_name: data.agent_names?.join('、') || '智能体',
      status: 'testing',
      message: data.message
    }
  } else if (data.type === 'test_case_generation_completed') {
    testProgress.value['generation'] = {
      agent_id: 'generation',
      agent_name: data.agent_names?.join('、') || '智能体',
      status: 'completed',
      message: data.message,
      folder_name: data.folder_name,
      test_case_count: data.test_case_count
    }
    testModeStatus.value = 'completed'
    messages.value.push({
      role: 'assistant',
      content: data.message || '测试用例生成完成！'
    })
    scrollToBottom()
  } else if (data.type === 'test_case_generation_error') {
    testProgress.value['generation'] = {
      agent_id: 'generation',
      agent_name: data.agent_names?.join('、') || '智能体',
      status: 'error',
      message: data.message
    }
    testModeStatus.value = 'error'
    messages.value.push({
      role: 'assistant',
      content: data.message || '测试用例生成失败'
    })
    scrollToBottom()
  }
}

const disconnectWebSocket = () => {
  if (ws) {
    ws.close()
    ws = null
  }
  if (wsReconnectTimer) {
    clearTimeout(wsReconnectTimer)
    wsReconnectTimer = null
  }
}

onMounted(async () => {
  loadHistory()
  loadAgentsAndTestFolders()
  if (chatMode.value === 'chat') {
    loadKnowledgeBases()
  }
  
  if (chatMode.value === 'test') {
    connectWebSocket()
  }
  
  if (currentChatId.value && messages.value.length === 0) {
    try {
      const response = await axios.get(`/api/conversations/${currentChatId.value}`)
      const data = response.data
      chatTitle.value = data.title
      chatMode.value = data.conversation_mode || 'chat'
      messages.value = data.messages.map(m => ({
        ...m,
        collapsed: m.role === 'reasoning'
      }))
      
      try {
        const uiResponse = await axios.get(`/api/unified-agent-chat/workflow-ui/conversation/${currentChatId.value}`)
        const workflowUis = uiResponse.data.workflow_uis || []
        
        const updatedMessages = [...messages.value]
        workflowUis.forEach(ui => {
          const msgIndex = updatedMessages.findIndex(m => m.id === ui.message_id)
          if (msgIndex !== -1) {
            updatedMessages[msgIndex] = {
              ...updatedMessages[msgIndex],
              ui_config: ui.ui_config
            }
          }
        })
        messages.value = updatedMessages
      } catch (e) {
        console.log('No workflow UI data for this conversation')
      }
      
      if (data.test_state) {
        testModeStatus.value = data.test_state.status
        testModeAgentNames.value = data.test_state.agent_names
        testModeTestCase.value = data.test_state.test_case
        requestInterval.value = data.test_state.request_interval || 0
        
        if (data.test_state.status === 'start_testing') {
          await loadAgentsAndTestFolders()
          selectedAgentNames.value = [...data.test_state.agent_names]
          selectedTestCase.value = data.test_state.test_case
        }
      } else {
        testModeStatus.value = 'pending'
        testModeAgentNames.value = []
        testModeTestCase.value = ''
        requestInterval.value = 0
      }
      
      scrollToBottom()
    } catch (error) {
      console.error('Failed to load chat on mount:', error)
    }
  }
})

onUnmounted(() => {
  disconnectWebSocket()
})

watch(chatMode, (newMode) => {
  if (newMode === 'test') {
    connectWebSocket()
  } else {
    disconnectWebSocket()
  }
})

const availableAgents = ref([])
const availableTestFolders = ref([])
const selectedAgentNames = ref([])
const selectedTestCase = ref('')

const showHistory = ref(false)
const historyButtonPosition = ref(50)
const isHistoryDragging = ref(false)
let historyDragStartY = 0
let historyDragStartPosition = 0
let historyHasDragged = false
const historyPage = ref(1)
const hasMoreHistory = ref(false)
const historyLoading = ref(false)

const username = computed(() => localStorage.getItem('username') || 'User')

const showToast = (message, type = 'error') => {
  toast.value = { show: true, message, type }
  setTimeout(() => {
    toast.value.show = false
  }, 3000)
}

const autoResizeTextarea = () => {
  const textarea = inputRef.value
  if (textarea) {
    textarea.style.height = 'auto'
    const newHeight = Math.min(textarea.scrollHeight, 120)
    textarea.style.height = newHeight + 'px'
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesArea.value && !userScrollingMain.value) {
      messagesArea.value.scrollTop = messagesArea.value.scrollHeight
    }
  })
}

const onMessagesScroll = () => {
  if (messagesArea.value) {
    const el = messagesArea.value
    const isAtBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 50
    userScrollingMain.value = !isAtBottom
  }
}

const setReasoningRef = (el, index) => {
  reasoningRefs.value[index] = el
}

const onReasoningScroll = (event, index) => {
  const el = event.target
  const isAtBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 50
  userScrolling.value[index] = !isAtBottom
}

const scrollToReasoningBottom = (index) => {
  const el = reasoningRefs.value[index]
  if (el && !userScrolling.value[index]) {
    el.scrollTop = el.scrollHeight
  }
}

const getLocalCache = () => {
  try {
    const data = localStorage.getItem(CACHE_KEY)
    return data ? JSON.parse(data) : []
  } catch {
    return []
  }
}

const saveLocalCache = () => {
  try {
    const cache = chatHistory.value.slice(0, MAX_CACHE)
    localStorage.setItem(CACHE_KEY, JSON.stringify(cache))
  } catch (e) {
    console.error('Failed to save cache:', e)
  }
}

const loadHistory = async (page = 1, append = false) => {
  if (historyLoading.value) return
  
  historyLoading.value = true
  
  try {
    const response = await axios.get(`/api/conversations`, {
      params: { page, page_size: PAGE_SIZE }
    })
    const data = response.data
    
    if (append) {
      const existingIds = new Set(chatHistory.value.map(c => c.id))
      const newItems = data.items.filter(c => !existingIds.has(c.id))
      chatHistory.value = [...chatHistory.value, ...newItems]
    } else {
      chatHistory.value = data.items
    }
    
    historyPage.value = page
    hasMoreHistory.value = data.has_more
    
    saveLocalCache()
  } catch (error) {
    console.error('Failed to load history:', error)
    
    if (!append) {
      const cache = getLocalCache()
      if (cache.length > 0) {
        chatHistory.value = cache
        hasMoreHistory.value = false
      }
    }
  } finally {
    historyLoading.value = false
  }
}

const loadMoreHistory = () => {
  if (hasMoreHistory.value && !historyLoading.value) {
    loadHistory(historyPage.value + 1, true)
  }
}

const onHistoryScroll = (e) => {
  const target = e.target
  if (target.scrollHeight - target.scrollTop - target.clientHeight < 50) {
    loadMoreHistory()
  }
}

const startHistoryDrag = (e) => {
  e.preventDefault()
  historyDragStartY = e.clientY
  historyDragStartPosition = historyButtonPosition.value
  historyHasDragged = false
  isHistoryDragging.value = true
  
  document.addEventListener('mousemove', onHistoryDrag)
  document.addEventListener('mouseup', stopHistoryDrag)
}

const onHistoryDrag = (e) => {
  if (!isHistoryDragging.value) return
  
  const deltaY = e.clientY - historyDragStartY
  if (Math.abs(deltaY) > 3) {
    historyHasDragged = true
  }
  
  const mainContent = document.querySelector('.main-content')
  if (!mainContent) return
  
  const mainHeight = mainContent.offsetHeight
  const deltaPercent = (deltaY / mainHeight) * 100
  
  let newPosition = historyDragStartPosition + deltaPercent
  newPosition = Math.max(5, Math.min(95, newPosition))
  
  historyButtonPosition.value = newPosition
}

const stopHistoryDrag = () => {
  isHistoryDragging.value = false
  document.removeEventListener('mousemove', onHistoryDrag)
  document.removeEventListener('mouseup', stopHistoryDrag)
}

const handleHistoryToggle = () => {
  if (historyHasDragged) {
    historyHasDragged = false
    return
  }
  showHistory.value = !showHistory.value
}

const loadChat = async (chat) => {
  try {
    const response = await axios.get(`/api/conversations/${chat.id}`)
    const data = response.data
    currentChatId.value = data.id
    chatTitle.value = data.title
    chatMode.value = data.conversation_mode || 'chat'
    messages.value = data.messages.map(m => ({
      ...m,
      collapsed: m.role === 'reasoning'
    }))
    
    try {
      const uiResponse = await axios.get(`/api/unified-agent-chat/workflow-ui/conversation/${chat.id}`)
      const workflowUis = uiResponse.data.workflow_uis || []
      
      const updatedMessages = [...messages.value]
      workflowUis.forEach(ui => {
        const msgIndex = updatedMessages.findIndex(m => m.id === ui.message_id)
        if (msgIndex !== -1) {
          updatedMessages[msgIndex] = {
            ...updatedMessages[msgIndex],
            ui_config: ui.ui_config
          }
        }
      })
      messages.value = updatedMessages
    } catch (e) {
      console.log('No workflow UI data for this conversation')
    }
    
    if (data.test_state) {
      testModeStatus.value = data.test_state.status
      testModeAgentNames.value = data.test_state.agent_names
      testModeTestCase.value = data.test_state.test_case
      requestInterval.value = data.test_state.request_interval || 0
      
      if (data.test_state.status === 'start_testing') {
        await loadAgentsAndTestFolders()
        selectedAgentNames.value = [...data.test_state.agent_names]
        selectedTestCase.value = data.test_state.test_case
      }
    } else {
      testModeStatus.value = 'pending'
      testModeAgentNames.value = []
      testModeTestCase.value = ''
      requestInterval.value = 0
    }
    
    showHistory.value = false
    scrollToBottom()
  } catch (error) {
    console.error('Failed to load chat:', error)
    showToast('加载对话失败')
  }
}

const deleteChat = async (id) => {
  const chat = chatHistory.value.find(c => c.id === id)
  if (!chat) return
  
  let confirmMessage = '确定要删除这个对话吗？'
  if (chat.conversation_mode === 'test') {
    confirmMessage = '这是一个测试对话，删除后将同时删除相关的测试结果。确定要删除吗？'
  }
  
  if (!confirm(confirmMessage)) {
    return
  }
  
  try {
    await axios.delete(`/api/conversations/${id}`)
    chatHistory.value = chatHistory.value.filter(c => c.id !== id)
    saveLocalCache()
    
    if (currentChatId.value === id) {
      currentChatId.value = null
      messages.value = []
    }
  } catch (error) {
    console.error('Failed to delete chat:', error)
    showToast('删除失败')
  }
}

const saveRequestInterval = async () => {
  if (!currentChatId.value) return
  
  try {
    await axios.post('/api/test-chat/update-interval', {
      conversation_id: currentChatId.value,
      request_interval: requestInterval.value || 0
    })
  } catch (error) {
    console.error('Failed to save request interval:', error)
  }
}

const loadAgentsAndTestFolders = async () => {
  try {
    const results = await Promise.allSettled([
      axios.get('/api/unified-agent-chat/agents'),
      axios.get('/api/test-chat/test-folders')
    ])
    
    const allAgents = []
    
    if (results[0].status === 'fulfilled') {
      const agents = results[0].value.data || []
      console.log('Loaded agents:', agents)
      allAgents.push(...agents)
    } else {
      console.error('Failed to load agents:', results[0].reason)
    }
    
    if (results[1].status === 'fulfilled') {
      availableTestFolders.value = results[1].value.data || []
    } else {
      console.error('Failed to load test folders:', results[1].reason)
    }
    
    console.log('All agents:', allAgents)
    availableAgents.value = allAgents
  } catch (error) {
    console.error('Failed to load agents and test folders:', error)
  }
}

const saveTestConfig = async () => {
  if (!currentChatId.value) return
  
  try {
    const response = await axios.post('/api/test-chat/update-test-config', {
      conversation_id: currentChatId.value,
      agent_names: selectedAgentNames.value,
      test_case: selectedTestCase.value
    })
    
    const data = response.data
    testModeAgentNames.value = data.agent_names
    testModeTestCase.value = data.test_case
    
    if (data.updated_message_content) {
      for (let i = messages.value.length - 1; i >= 0; i--) {
        if (messages.value[i].role === 'assistant') {
          messages.value[i].content = data.updated_message_content
          break
        }
      }
    }
    
    showToast('配置已保存', 'success')
  } catch (error) {
    console.error('Failed to save test config:', error)
    showToast('保存失败')
  }
}

const confirmStartTest = async () => {
  if (!currentChatId.value) {
    showToast('请先创建对话', 'error')
    return
  }
  
  if (selectedAgentNames.value.length === 0 || !selectedTestCase.value) {
    showToast('请选择智能体和测试用例', 'error')
    return
  }
  
  try {
    const response = await axios.post('/api/test-chat/start-test', {
      conversation_id: currentChatId.value,
      agent_names: selectedAgentNames.value,
      test_case_folder_name: selectedTestCase.value,
      request_interval: requestInterval.value || 0
    })
    
    testModeStatus.value = 'testing'
    
    messages.value.push({
      role: 'assistant',
      content: '开始测试...'
    })
    
    scrollToBottom()
    showToast('测试已启动', 'success')
  } catch (error) {
    console.error('Failed to start test:', error)
    showToast(error.response?.data?.detail || '启动测试失败', 'error')
  }
}

const startNewChat = () => {
  currentChatId.value = null
  chatTitle.value = ''
  messages.value = []
  showHistory.value = false
  testModeStatus.value = 'pending'
  testModeAgentNames.value = []
  testModeTestCase.value = ''
  requestInterval.value = 0
  selectedAgentNames.value = []
  selectedTestCase.value = ''
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  if (diff < 604800000) return Math.floor(diff / 86400000) + '天前'
  
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

const handleSendText = async (text) => {
  if (!text || loading.value) return
  inputMessage.value = text
  await sendMessage()
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || loading.value) return
  
  if (!selectedModel.value) {
    showToast('请先选择一个模型')
    return
  }
  
  const userMessage = inputMessage.value.trim()
  messages.value.push({
    role: 'user',
    content: userMessage
  })
  
  inputMessage.value = ''
  if (inputRef.value) {
    if (inputRef.value.style) {
      inputRef.value.style.height = 'auto'
    }
  }
  scrollToBottom()
  
  if (chatMode.value === 'test') {
    await handleTestMode(userMessage)
    return
  }
  
  loading.value = true
  abortController.value = new AbortController()
  
  const requestMessages = messages.value
    .filter(m => m.role !== 'reasoning')
    .map(m => ({
      role: m.role,
      content: m.content
    }))
  
  try {
    const token = localStorage.getItem('token')
    
    let apiEndpoint
    
    if (chatMode.value === 'agent') {
      apiEndpoint = '/api/unified-agent-chat/stream'
    } else if (chatMode.value === 'chat' && selectedKB.value) {
      apiEndpoint = '/api/rag-chat/stream'
    } else {
      apiEndpoint = '/api/chat/stream'
    }
    
    const requestBody = {
      config_id: selectedModel.value.id,
      messages: requestMessages,
      conversation_id: currentChatId.value,
      enable_thinking: enableThinking.value,
      enable_search: enableSearch.value,
      file_paths: uploadedFiles.value.map(f => f.path),
      file_items: uploadedFiles.value.map(f => ({ name: f.name }))
    }
    
    if (chatMode.value === 'chat' && selectedKB.value) {
      requestBody.knowledge_base_id = selectedKB.value.id
    }
    
    const response = await fetch(apiEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(requestBody),
      signal: abortController.value.signal
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '请求失败')
    }
    
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let reasoningAdded = false
    let assistantAdded = false
    
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      
      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') {
            break
          }
          try {
            const parsed = JSON.parse(data)
            if (parsed.error) {
              showToast(parsed.error)
              break
            }
            if (parsed.type === 'saved') {
              console.log('Saved:', parsed)
              if (parsed.conversation_id && !currentChatId.value) {
                currentChatId.value = parsed.conversation_id
                chatTitle.value = messages.value[0]?.content?.substring(0, 50) || '新对话'
                chatHistory.value.unshift({
                  id: parsed.conversation_id,
                  title: chatTitle.value,
                  conversation_mode: chatMode.value,
                  created_at: new Date().toISOString()
                })
              }
              if (parsed.ui_config) {
                const lastMsg = messages.value[messages.value.length - 1]
                if (lastMsg) {
                  lastMsg.ui_config = parsed.ui_config
                }
              }
              continue
            }
            if (parsed.type === 'ui_config') {
              console.log('UI Config:', parsed.ui_config)
              const lastMsg = messages.value[messages.value.length - 1]
              if (lastMsg) {
                // 使用 Vue.set 确保响应式更新
                lastMsg.ui_config = parsed.ui_config
                // 强制触发响应式更新
                messages.value = [...messages.value]
              }
              continue
            }
            if (parsed.type === 'verbose') {
              if (!assistantAdded) {
                messages.value.push({
                  role: 'assistant',
                  content: ''
                })
                assistantAdded = true
              }
              messages.value[messages.value.length - 1].content += parsed.content
              scrollToBottom()
              continue
            }
            if (parsed.reasoning) {
              if (!reasoningAdded) {
                messages.value.push({
                  role: 'reasoning',
                  content: '',
                  collapsed: false
                })
                reasoningAdded = true
              }
              const reasoningIndex = messages.value.length - 1
              messages.value[reasoningIndex].content += parsed.reasoning
              scrollToBottom()
              nextTick(() => scrollToReasoningBottom(reasoningIndex))
            }
            if (parsed.content) {
              // 当开始显示 assistant 内容时，自动折叠 reasoning 消息
              if (reasoningAdded && !assistantAdded) {
                const reasoningMsg = messages.value.find(m => m.role === 'reasoning' && !m.collapsed)
                if (reasoningMsg) {
                  reasoningMsg.collapsed = true
                }
              }
              if (!assistantAdded) {
                messages.value.push({
                  role: 'assistant',
                  content: ''
                })
                assistantAdded = true
              }
              messages.value[messages.value.length - 1].content += parsed.content
              scrollToBottom()
            }
          } catch (e) {
            // Ignore parse errors
          }
        }
      }
    }
    
    // 移除空的 assistant 消息
    if (assistantAdded && !messages.value[messages.value.length - 1].content) {
      messages.value.pop()
      assistantAdded = false
    }
    
    // 如果没有任何响应
    if (!reasoningAdded && !assistantAdded) {
      showToast('模型未返回响应')
    }
    
  } catch (error) {
    if (error.name === 'AbortError') {
      // 用户中断，不需要额外处理
    } else {
      console.error('Chat error:', error)
      showToast(error.message || '发送消息失败')
    }
  } finally {
    loading.value = false
    abortController.value = null
    scrollToBottom()
  }
}

const stopGeneration = () => {
  if (abortController.value) {
    abortController.value.abort()
  }
}

const handleTestMode = async (userMessage) => {
  loading.value = true
  
  try {
    const requestMessages = messages.value
      .filter(m => m.role !== 'reasoning')
      .map(m => ({
        role: m.role,
        content: m.content
      }))
    
    const response = await fetch('/api/test-chat/recognize-intent', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        messages: requestMessages,
        conversation_id: currentChatId.value,
        current_status: testModeStatus.value,
        current_agent_names: testModeAgentNames.value,
        current_test_case: testModeTestCase.value,
        current_request_interval: requestInterval.value,
        config_id: selectedModel.value?.id,
        enable_thinking: enableThinking.value,
        enable_search: enableSearch.value
      })
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '意图识别失败')
    }
    
    const contentType = response.headers.get('content-type')
    
    if (contentType && contentType.includes('text/event-stream')) {
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let reasoningAdded = false
      let assistantAdded = false
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            if (data === '[DONE]') {
              break
            }
            try {
              const parsed = JSON.parse(data)
              if (parsed.error) {
                showToast(parsed.error)
                break
              }
              if (parsed.reasoning) {
                if (!reasoningAdded) {
                  messages.value.push({
                    role: 'reasoning',
                    content: '',
                    collapsed: false
                  })
                  reasoningAdded = true
                }
                const lastMsg = messages.value[messages.value.length - 1]
                lastMsg.content += parsed.reasoning
              }
              if (parsed.content) {
                if (!assistantAdded) {
                  messages.value.push({
                    role: 'assistant',
                    content: ''
                  })
                  assistantAdded = true
                }
                const lastMsg = messages.value[messages.value.length - 1]
                lastMsg.content += parsed.content
              }
              if (parsed.type === 'verbose') {
                if (!assistantAdded) {
                  messages.value.push({
                    role: 'assistant',
                    content: ''
                  })
                  assistantAdded = true
                }
                const lastMsg = messages.value[messages.value.length - 1]
                lastMsg.content += parsed.content
              }
              if (parsed.type === 'saved') {
                console.log('Test mode saved:', parsed)
                if (parsed.conversation_id && !currentChatId.value) {
                  currentChatId.value = parsed.conversation_id
                  chatTitle.value = messages.value[0]?.content?.substring(0, 50) || '新对话'
                  chatHistory.value.unshift({
                    id: parsed.conversation_id,
                    title: chatTitle.value,
                    conversation_mode: 'test',
                    created_at: new Date().toISOString()
                  })
                }
              }
            } catch (e) {
              // Ignore parse errors
            }
          }
        }
        scrollToBottom()
      }
    } else {
      const result = await response.json()
      
      testModeStatus.value = result.status
      testModeAgentNames.value = result.agent_names
      testModeTestCase.value = result.test_case
      if (result.request_interval !== undefined) {
        requestInterval.value = result.request_interval
      }
      
      messages.value.push({
        role: 'assistant',
        content: result.message
      })
      
      scrollToBottom()
      
      if (result.conversation_id && !currentChatId.value) {
        currentChatId.value = result.conversation_id
        chatTitle.value = messages.value[0]?.content?.substring(0, 50) || '新对话'
        chatHistory.value.unshift({
          id: result.conversation_id,
          title: chatTitle.value,
          conversation_mode: 'test',
          created_at: new Date().toISOString()
        })
      }
    }
    
  } catch (error) {
    console.error('Test mode error:', error)
    showToast(error.message || '测试模式处理失败')
  } finally {
    loading.value = false
  }
}

const loadKnowledgeBases = async () => {
  try {
    const response = await axios.get('/api/knowledge-bases')
    knowledgeBases.value = response.data
  } catch (error) {
    console.error('Failed to load knowledge bases:', error)
  }
}

const triggerFileUpload = () => {
  if (fileInputRef.value) {
    fileInputRef.value.click()
  }
}

const handleFileUpload = async (event) => {
  const files = event.target.files
  if (!files || files.length === 0) return
  
  for (const file of files) {
    const allowedTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/msword',
      'application/vnd.ms-powerpoint',
      'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    ]
    
    const allowedExtensions = ['.pdf', '.xlsx', '.xls', '.docx', '.doc', '.ppt', '.pptx', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp']
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase()
    
    if (!allowedExtensions.includes(fileExtension)) {
      showToast(`不支持的文件类型: ${file.name}`, 'error')
      continue
    }
    
    if (file.size > 50 * 1024 * 1024) {
      showToast(`文件过大: ${file.name}`, 'error')
      continue
    }
    
    try {
      let kbId = uploadingFileKBId.value
      
      if (!kbId) {
        const uploadKB = knowledgeBases.value.find(kb => kb.name === '上传的文件')
        if (uploadKB) {
          kbId = uploadKB.id
          uploadingFileKBId.value = kbId
        } else {
          const createResponse = await axios.post('/api/knowledge-bases', {
            name: '上传的文件',
            description: '自动创建的上传文件知识库'
          })
          kbId = createResponse.data.id
          uploadingFileKBId.value = kbId
          await loadKnowledgeBases()
        }
      }
      
      const formData = new FormData()
      formData.append('file', file)
      formData.append('knowledge_base_id', kbId)
      
      const response = await axios.post('/api/test-case-files', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      
      const fileId = response.data.id
      const filePath = response.data.file_path
      const embeddingStatus = response.data.embedding_status || 'processing'
      
      uploadedFiles.value.push({
        name: file.name,
        path: filePath,
        id: fileId,
        embedding_status: embeddingStatus,
        embedding_error: response.data.embedding_error || null
      })
      
      if (embeddingStatus === 'processing') {
        startFileStatusPolling(fileId)
      }
      
      showToast(`文件上传成功: ${file.name}`, 'success')
    } catch (error) {
      console.error('File upload failed:', error)
      const errorMsg = error.response?.data?.detail || error.message || '未知错误'
      showToast(`文件上传失败: ${file.name} - ${errorMsg}`, 'error')
    }
  }
  
  event.target.value = ''
}

const removeFile = (index) => {
  const file = uploadedFiles.value[index]
  if (file && file.id && fileStatusPollingTimers.value[file.id]) {
    clearInterval(fileStatusPollingTimers.value[file.id])
    delete fileStatusPollingTimers.value[file.id]
  }
  uploadedFiles.value.splice(index, 1)
}

const startFileStatusPolling = (fileId) => {
  if (fileStatusPollingTimers.value[fileId]) {
    clearInterval(fileStatusPollingTimers.value[fileId])
  }
  
  fileStatusPollingTimers.value[fileId] = setInterval(async () => {
    try {
      const response = await axios.get(`/api/test-case-files/${fileId}/status`)
      const data = response.data
      const fileIndex = uploadedFiles.value.findIndex(f => f.id === fileId)
      
      if (fileIndex !== -1) {
        uploadedFiles.value[fileIndex].embedding_status = data.embedding_status || 'pending'
        uploadedFiles.value[fileIndex].embedding_error = data.embedding_error || null
        
        if (data.embedding_status === 'completed' || data.embedding_status === 'failed') {
          clearInterval(fileStatusPollingTimers.value[fileId])
          delete fileStatusPollingTimers.value[fileId]
        }
      } else {
        clearInterval(fileStatusPollingTimers.value[fileId])
        delete fileStatusPollingTimers.value[fileId]
      }
    } catch (error) {
      console.error('Failed to fetch file status:', error)
    }
  }, 2000)
}

const stopAllFileStatusPolling = () => {
  Object.keys(fileStatusPollingTimers.value).forEach(fileId => {
    clearInterval(fileStatusPollingTimers.value[fileId])
  })
  fileStatusPollingTimers.value = {}
}

const triggerFileInput = () => {
  if (!fileInputRef.value) return
  fileInputRef.value.click()
}

const openExistingFilesModal = async () => {
  showExistingFilesModal.value = true
  loadingExistingFiles.value = true
  selectedExistingFiles.value = []
  
  try {
    const response = await axios.get('/api/test-case-files/uploaded')
    existingFiles.value = response.data.files || []
  } catch (error) {
    console.error('Failed to load uploaded files:', error)
    showToast('加载已上传文件失败', 'error')
    existingFiles.value = []
  } finally {
    loadingExistingFiles.value = false
  }
}

const closeExistingFilesModal = () => {
  showExistingFilesModal.value = false
  selectedExistingFiles.value = []
}

const isFileSelected = (filePath) => {
  return selectedExistingFiles.value.some(f => f.file_path === filePath)
}

const toggleExistingFile = (file) => {
  const index = selectedExistingFiles.value.findIndex(f => f.file_path === file.file_path)
  if (index === -1) {
    selectedExistingFiles.value.push(file)
  } else {
    selectedExistingFiles.value.splice(index, 1)
  }
}

const confirmExistingFiles = () => {
  for (const file of selectedExistingFiles.value) {
    const alreadyAdded = uploadedFiles.value.some(f => f.path === file.file_path)
    if (!alreadyAdded) {
      uploadedFiles.value.push({
        name: file.filename,
        path: file.file_path,
        id: file.id,
        embedding_status: file.embedding_status,
        embedding_error: null
      })
    }
  }
  
  showToast(`已添加 ${selectedExistingFiles.value.length} 个文件`, 'success')
  closeExistingFilesModal()
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  return `${size.toFixed(1)} ${units[unitIndex]}`
}

const selectKB = (kb) => {
  selectedKB.value = kb
  showKBDropdown.value = false
}

const toggleKBDropdown = () => {
  showKBDropdown.value = !showKBDropdown.value
}

const closeKBDropdownOnClickOutside = (e) => {
  if (!e.target.closest('.kb-selector')) {
    showKBDropdown.value = false
    document.removeEventListener('click', closeKBDropdownOnClickOutside)
  }
}

watch(showKBDropdown, (val) => {
  if (val) {
    document.addEventListener('click', closeKBDropdownOnClickOutside)
  } else {
    document.removeEventListener('click', closeKBDropdownOnClickOutside)
  }
})

watch(chatMode, (newMode) => {
  if (newMode === 'chat' && knowledgeBases.value.length === 0) {
    loadKnowledgeBases()
  }
  testModeStatus.value = 'pending'
  testModeAgentNames.value = []
  testModeTestCase.value = ''
  requestInterval.value = 0
  selectedAgentNames.value = []
  selectedTestCase.value = ''
  uploadedFiles.value = []
  stopAllFileStatusPolling()
})

watch(testModeStatus, (newStatus) => {
  if (newStatus === 'start_testing') {
    loadAgentsAndTestFolders()
    selectedAgentNames.value = [...testModeAgentNames.value]
    selectedTestCase.value = testModeTestCase.value
  }
})

</script>

<style scoped>
.chat-container {
  display: flex;
  height: 100%;
  background: #f5f7fa;
  overflow: hidden;
  position: relative;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  transition: margin-right 0.3s ease, margin-left 0.3s ease;
  position: relative;
}

.main-content.sidebar-open {
  margin-right: 280px;
}

.main-content.test-progress-open {
  margin-left: 320px;
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.messages-area::-webkit-scrollbar {
  display: none;
}

.messages-wrapper {
  max-width: 800px;
  margin: 0 auto;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 400px;
  color: #999;
}

.empty-icon {
  width: 80px;
  height: 80px;
  margin-bottom: 16px;
  color: #667eea;
  opacity: 0.5;
}

.empty-icon svg {
  width: 100%;
  height: 100%;
}

.empty-state h3 {
  font-size: 20px;
  color: #333;
  margin-bottom: 8px;
}

.empty-state p {
  font-size: 14px;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-weight: 600;
  font-size: 14px;
}

.message.user .message-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.message.assistant .message-avatar {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  color: #667eea;
}

.message.assistant .message-avatar svg {
  width: 20px;
  height: 20px;
}

.message-content {
  max-width: 70%;
}

.message-reasoning {
  margin-bottom: 8px;
  background: #f8f9fa;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e9ecef;
}

.reasoning-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: #e9ecef;
  color: #6c757d;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  user-select: none;
}

.reasoning-header:hover {
  background: #dee2e6;
}

.reasoning-header svg {
  opacity: 0.7;
}

.reasoning-header .collapse-icon {
  margin-left: auto;
  transition: transform 0.2s;
}

.message-reasoning.collapsed .collapse-icon {
  transform: rotate(-90deg);
}

.reasoning-content {
  padding: 10px 12px;
  font-size: 13px;
  color: #6c757d;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 200px;
  overflow-y: auto;
}

.reasoning-message .message-content {
  max-width: 85%;
}

.reasoning-message .message-reasoning {
  margin-bottom: 0;
}

.message-text {
  padding: 8px 10px;
  border-radius: 12px;
  line-height: 1.5;
  font-size: 14px;
  word-break: break-word;
}

.message.user .message-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.message.user .message-text :deep(.md-preview),
.message.user .message-text :deep(.markdown-renderer),
.message.user .message-text :deep(.md-preview-wrapper),
.message.user .message-text :deep(.md-preview-content),
.message.user .message-text :deep(.md-editor),
.message.user .message-text :deep(.md-editor-preview) {
  background: transparent !important;
  background-color: transparent !important;
  color: #fff !important;
}

.message.user .message-text :deep(p),
.message.user .message-text :deep(span),
.message.user .message-text :deep(li),
.message.user .message-text :deep(h1),
.message.user .message-text :deep(h2),
.message.user .message-text :deep(h3),
.message.user .message-text :deep(h4),
.message.user .message-text :deep(h5),
.message.user .message-text :deep(h6) {
  color: #fff !important;
}

.message.user .message-text :deep(code) {
  background: rgba(255, 255, 255, 0.2);
}

.message.user .message-text :deep(pre),
.message.user .message-text :deep(blockquote) {
  background: rgba(255, 255, 255, 0.1) !important;
}

.message.assistant .message-text {
  background: #fff;
  color: #333;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.message.assistant .message-text pre {
  margin: 8px -16px;
  border-radius: 0;
}

.message.assistant .message-text pre:first-child {
  margin-top: -12px;
}

.message.assistant .message-text pre:last-child {
  margin-bottom: -12px;
}

.message.assistant .message-text code {
  font-size: 13px;
}

.message.assistant .message-text pre code {
  padding: 12px 16px;
}

.message.assistant .message-text :deep(.katex-block),
.message .message-text :deep(.katex-block),
.message.assistant .message-text :deep(.katex-display),
.message .message-text :deep(.katex-display),
.message.assistant .message-text :deep(p:has(.katex-display)),
.message .message-text :deep(p:has(.katex-display)) {
  overflow-x: auto !important;
  overflow-y: hidden !important;
  max-width: 100% !important;
  display: block !important;
  padding: 4px 12px !important;
  margin: 0.3em 0 !important;
}

.message.assistant .message-text :deep(.katex),
.message .message-text :deep(.katex) {
  white-space: nowrap;
}

.message.no-avatar {
  margin-top: -8px;
}

.message.no-avatar .message-content {
  margin-left: 48px;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: #fff;
  border-radius: 16px;
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #667eea;
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.test-config-panel {
  margin: 16px 0;
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.test-config-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  font-weight: 500;
}

.test-config-body {
  padding: 16px;
}

.config-item {
  margin-bottom: 16px;
}

.config-item:last-child {
  margin-bottom: 0;
}

.config-item label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
  font-size: 14px;
}

.agent-checkboxes {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #f5f7fa;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.checkbox-label:hover {
  border-color: #667eea;
}

.checkbox-label input:checked + span {
  color: #667eea;
  font-weight: 500;
}

.checkbox-label input {
  accent-color: #667eea;
}

.test-case-select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  background: #fff;
  cursor: pointer;
}

.test-case-select:focus {
  outline: none;
  border-color: #667eea;
}

.config-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #eee;
}

.btn-save-config,
.btn-start-test {
  flex: 1;
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-save-config {
  background: #f5f7fa;
  color: #666;
  border: 1px solid #ddd;
}

.btn-save-config:hover:not(:disabled) {
  background: #e8eaed;
}

.btn-start-test {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.btn-start-test:hover:not(:disabled) {
  opacity: 0.9;
  transform: translateY(-1px);
}

.btn-save-config:disabled,
.btn-start-test:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.input-area {
  padding: 16px 24px;
  background: #fff;
  border-top: 1px solid #eee;
}

.input-options {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.upload-file-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  height: 28px;
  border: 1px solid #ddd;
  border-radius: 16px;
  background: #fff;
  color: #666;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  box-sizing: border-box;
}

.upload-file-btn svg {
  width: 14px;
  height: 14px;
}

.upload-file-btn:hover {
  border-color: #667eea;
  color: #667eea;
}

.uploaded-files-list {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-bottom: 8px;
}

.uploaded-file-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  background: #f0f4ff;
  border: 1px solid #e0e7ff;
  border-radius: 8px;
  font-size: 12px;
  min-width: 0;
}

.uploaded-file-item .file-icon {
  width: 14px;
  height: 14px;
  color: #667eea;
  flex-shrink: 0;
}

.uploaded-file-item .file-name {
  flex: 1;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.uploaded-file-item .remove-file-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: #999;
  cursor: pointer;
  transition: all 0.2s;
}

.uploaded-file-item .remove-file-btn svg {
  width: 12px;
  height: 12px;
}

.uploaded-file-item .remove-file-btn:hover {
  background: #e0e7ff;
  color: #667eea;
}

.uploaded-file-item .file-embedding-status {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  color: #999;
  flex-shrink: 0;
}

.uploaded-file-item .file-embedding-status.processing {
  color: #f59e0b;
  background: #fef3c7;
}

.uploaded-file-item .file-embedding-status.completed {
  color: #10b981;
  background: #d1fae5;
}

.uploaded-file-item .file-embedding-status.failed {
  color: #ef4444;
  background: #fee2e2;
}

.uploaded-file-item .file-embedding-status .loading-spinner {
  width: 10px;
  height: 10px;
  border: 2px solid #f59e0b;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.input-wrapper {
  max-width: 800px;
  margin: 0 auto;
  background: #f5f7fa;
  border-radius: 16px;
  padding: 12px 12px 8px 12px;
}

.input-row {
  display: flex;
  align-items: flex-end;
  gap: 12px;
}

.thinking-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  height: 28px;
  border: 1px solid #ddd;
  border-radius: 16px;
  background: #fff;
  color: #666;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  box-sizing: border-box;
}

.thinking-btn svg {
  width: 14px;
  height: 14px;
}

.thinking-btn:hover {
  border-color: #667eea;
  color: #667eea;
}

.thinking-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: transparent;
  color: #fff;
}

.search-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  height: 28px;
  border: 1px solid #ddd;
  border-radius: 16px;
  background: #fff;
  color: #666;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  box-sizing: border-box;
}

.search-btn svg {
  width: 14px;
  height: 14px;
}

.search-btn:hover {
  border-color: #667eea;
  color: #667eea;
}

.search-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: transparent;
  color: #fff;
}

.progress-toggle-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  height: 28px;
  border: 1px solid #ddd;
  border-radius: 16px;
  background: #fff;
  color: #666;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  box-sizing: border-box;
}

.progress-toggle-btn svg {
  width: 14px;
  height: 14px;
}

.progress-toggle-btn:hover {
  border-color: #667eea;
  color: #667eea;
}

.progress-toggle-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: transparent;
  color: #fff;
}

.interval-input-wrapper {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  height: 28px;
  border: 1px solid #ddd;
  border-radius: 16px;
  background: #fff;
  font-size: 12px;
  box-sizing: border-box;
}

.interval-input {
  width: 50px;
  height: 18px;
  border: none;
  outline: none;
  font-size: 12px;
  text-align: center;
  background: transparent;
  padding: 0;
}

.interval-input::-webkit-inner-spin-button,
.interval-input::-webkit-outer-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.interval-unit {
  color: #666;
  font-size: 12px;
  white-space: nowrap;
}

.kb-selector {
  position: relative;
}

.kb-select-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  height: 28px;
  max-width: 180px;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 12px;
  color: #666;
  white-space: nowrap;
  box-sizing: border-box;
}

.kb-select-btn span {
  overflow: hidden;
  text-overflow: ellipsis;
}

.kb-select-btn:hover {
  border-color: #667eea;
  color: #667eea;
}

.kb-select-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: transparent;
  color: #fff;
}

.kb-select-btn.active .kb-icon {
  color: #fff;
}

.kb-select-btn.active .dropdown-icon {
  color: #fff;
}

.kb-select-btn .kb-icon {
  width: 14px;
  height: 14px;
  color: #667eea;
}

.kb-select-btn .dropdown-icon {
  width: 14px;
  height: 14px;
  color: #666;
  transition: transform 0.2s;
}

.kb-dropdown {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 0;
  min-width: 100px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  z-index: 100;
  overflow: hidden;
}

.kb-dropdown .dropdown-empty {
  padding: 12px;
  text-align: center;
  color: #999;
  font-size: 13px;
}

.kb-dropdown .dropdown-item {
  padding: 8px 12px;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 1px solid #f0f0f0;
  max-width: 180px;
  overflow: hidden;
}

.kb-dropdown .dropdown-item:last-child {
  border-bottom: none;
}

.kb-dropdown .dropdown-item:hover {
  background: #f8f9ff;
}

.kb-dropdown .dropdown-item.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.kb-dropdown .kb-name {
  font-size: 13px;
  font-weight: 500;
  margin-bottom: 1px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.kb-dropdown .kb-count {
  font-size: 11px;
  opacity: 0.7;
}

.input-row textarea {
  flex: 1;
  border: none;
  background: transparent;
  resize: none;
  font-size: 14px;
  line-height: 1.5;
  min-height: 24px;
  max-height: 120px;
  overflow-y: auto;
  outline: none;
  font-family: inherit;
}

.input-row textarea::placeholder {
  color: #999;
}

.send-btn {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.send-btn svg {
  width: 20px;
  height: 20px;
}

.stop-btn {
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 12px;
  background: #ef4444;
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  flex-shrink: 0;
}

.stop-btn:hover {
  background: #dc2626;
  transform: scale(1.05);
}

.stop-btn svg {
  width: 18px;
  height: 18px;
}

.history-toggle {
  position: absolute;
  right: 8px;
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: grab;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  transition: background 0.2s, box-shadow 0.2s;
}

.history-toggle:active {
  cursor: grabbing;
}

.history-toggle:hover {
  background: #f0f0f0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.history-toggle svg {
  width: 24px;
  height: 24px;
  color: #667eea;
  pointer-events: none;
}

.history-sidebar {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 280px;
  background: #fff;
  border-left: 1px solid #eee;
  transform: translateX(100%);
  transition: transform 0.3s ease;
  display: flex;
  flex-direction: column;
  z-index: 50;
}

.history-sidebar.open {
  transform: translateX(0);
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid #eee;
}

.sidebar-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.new-chat-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.new-chat-btn:hover {
  transform: scale(1.05);
}

.new-chat-btn svg {
  width: 18px;
  height: 18px;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.empty-history {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #999;
  font-size: 14px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 4px;
}

.history-item:hover {
  background: #f5f7fa;
}

.history-item.active {
  background: #eef2ff;
}

.history-info {
  flex: 1;
  min-width: 0;
}

.history-title {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.history-meta {
  display: flex;
  gap: 8px;
  margin-top: 4px;
  font-size: 12px;
  color: #999;
}

.delete-btn {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #999;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all 0.2s;
}

.history-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  background: #fee2e2;
  color: #ef4444;
}

.delete-btn svg {
  width: 16px;
  height: 16px;
}

.loading-more,
.load-more {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  color: #999;
  font-size: 14px;
}

.load-more {
  cursor: pointer;
  color: #667eea;
}

.load-more:hover {
  background: #f5f7fa;
}

.delete-btn svg {
  width: 16px;
  height: 16px;
}

.toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  padding: 14px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  z-index: 3000;
  animation: slideIn 0.3s ease;
}

.toast.error {
  background: #ef4444;
  color: #fff;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.existing-files-modal {
  background: #fff;
  border-radius: 12px;
  width: 700px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  font-size: 18px;
  color: #1a1a2e;
  margin: 0;
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 50%;
  background: transparent;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #f0f0f0;
  color: #333;
}

.close-btn svg {
  width: 20px;
  height: 20px;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
  min-height: 200px;
  max-height: 50vh;
}

.loading-state,
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
  font-size: 14px;
}

.existing-files-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.existing-file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  background: #fff;
}

.existing-file-item:hover {
  border-color: #667eea;
  background: #f8f9ff;
}

.existing-file-item.selected {
  border-color: #667eea;
  background: #f0f4ff;
}

.existing-file-item .file-icon {
  width: 20px;
  height: 20px;
  color: #667eea;
  flex-shrink: 0;
}

.existing-file-item .file-name {
  flex: 1;
  color: #333;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.existing-file-item .file-size {
  color: #999;
  font-size: 12px;
  flex-shrink: 0;
}

.existing-file-item .file-type {
  color: #666;
  font-size: 12px;
  padding: 2px 6px;
  background: #f0f0f0;
  border-radius: 4px;
  flex-shrink: 0;
}

.existing-file-item .file-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  flex-shrink: 0;
}

.existing-file-item .file-status.completed {
  color: #10b981;
  background: #d1fae5;
}

.existing-file-item .file-status.processing {
  color: #f59e0b;
  background: #fef3c7;
}

.existing-file-item .file-status.failed {
  color: #ef4444;
  background: #fee2e2;
}

.existing-file-item .file-status.unknown {
  color: #6b7280;
  background: #f3f4f6;
}

.existing-file-item .check-icon {
  width: 20px;
  height: 20px;
  color: #667eea;
  flex-shrink: 0;
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-top: 1px solid #eee;
}

.selected-count {
  color: #666;
  font-size: 14px;
}

.btn-confirm {
  padding: 8px 20px;
  background: #667eea;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-confirm:hover:not(:disabled) {
  background: #5a6fd6;
}

.btn-confirm:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@keyframes slideIn {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
</style>
