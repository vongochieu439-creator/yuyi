// 羽翼Pro V2 - Vue应用主文件

const { createApp } = Vue;
const { ElMessage, ElNotification, ElMessageBox } = ElementPlus;

// 创建Vue应用
const app = createApp({
    data() {
        return {
            loading: false,
            currentView: 'list',  // 'list' | 'script' | 'keyframes' | 'editor' | 'export' | 'smart-create' | 'templates'
            selectedProject: null,
            exportDialogVisible: false,
            keyframeGenerationDialogVisible: false
        }
    },

    mounted() {
        this.init();
    },

    methods: {
        async init() {
            console.log('羽翼Pro V2 Web应用初始化...');
        },

        selectProject(project) {
            console.log('选中项目:', project);
            this.selectedProject = project;

            // 根据项目状态决定进入哪个视图
            const stage = project.generation_stage;
            if (stage === 'script') {
                // 脚本阶段 -> 进入脚本编辑页
                this.currentView = 'script';
            } else if (stage === 'keyframes') {
                // 关键帧阶段 -> 显示九宫格预览
                this.currentView = 'keyframes';
            } else if (stage === 'videos') {
                // 视频阶段 -> 显示视频编辑器
                this.currentView = 'editor';
            } else {
                // 默认显示脚本编辑
                this.currentView = 'script';
            }
        },

        goToKeyframes() {
            this.currentView = 'keyframes';
        },

        startSmartCreate() {
            this.currentView = 'smart-create';
        },

        onSmartCreateDone(project) {
            this.selectedProject = project;
            this.currentView = 'script';
        },

        backToList() {
            this.currentView = 'list';
            this.selectedProject = null;
        },

        openTemplates() {
            this.currentView = 'templates';
        },

        showExportDialog() {
            this.exportDialogVisible = true;
        },

        showKeyframeGenerationDialog() {
            this.keyframeGenerationDialogVisible = true;
        }
    }
});

// ==================== 项目列表组件 ====================

app.component('project-list', {
    template: `
        <div class="project-list-container">
            <div class="list-header">
                <h2>📁 视频项目列表</h2>
                <div>
                    <el-dropdown split-button type="primary" @click="$emit('smart-create')" @command="handleCreateCommand">
                        <el-icon><Plus /></el-icon> 智能创作
                        <template #dropdown>
                            <el-dropdown-menu>
                                <el-dropdown-item command="smart">智能创作 (推荐)</el-dropdown-item>
                                <el-dropdown-item command="quick">快速创建</el-dropdown-item>
                            </el-dropdown-menu>
                        </template>
                    </el-dropdown>
                    <el-button style="margin-left: 10px;" @click="$emit('open-ip-studio')" type="warning" plain>🎙️ 个人IP工作室</el-button>
                    <el-button style="margin-left: 10px;" @click="$emit('open-templates')" plain>📋 模板库</el-button>
                    <el-tag type="info" size="large" style="margin-left: 10px;">共 {{ projects.length }} 个项目</el-tag>
                </div>
            </div>

            <el-empty v-if="projects.length === 0 && !loading" description="暂无视频项目">
                <el-button type="primary" @click="$emit('smart-create')">智能创作</el-button>
                <el-button @click="showCreateDialog">快速创建</el-button>
                <el-button @click="refresh">刷新</el-button>
            </el-empty>

            <el-row :gutter="20" v-else>
                <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="project in projects" :key="project.project_id">
                    <el-card class="project-card" shadow="hover" @click="$emit('select-project', project)">
                        <div class="project-thumbnail">
                            <video v-if="project.thumbnail_url" :src="project.thumbnail_url + '#t=0.1'"
                                   class="thumbnail-video"
                                   @error="handleThumbnailError">
                            </video>
                            <div v-else class="thumbnail-placeholder">
                                <el-icon :size="40"><Film /></el-icon>
                                <p>{{ stageLabel(project.generation_stage) }}</p>
                            </div>
                            <div class="thumbnail-overlay">
                                <el-icon :size="40"><VideoPlay /></el-icon>
                            </div>
                        </div>
                        <div class="project-info">
                            <h3 class="project-title">{{ project.title }}</h3>
                            <p class="project-topic">{{ project.topic || '无主题' }}</p>
                            <div class="project-stats">
                                <el-tag size="small">{{ project.shot_count }}个分镜</el-tag>
                                <el-tag size="small" type="success">{{ (project.total_duration||0).toFixed(1) }}秒</el-tag>
                                <el-tag size="small" :type="stageTagType(project.generation_stage)">{{ stageLabel(project.generation_stage) }}</el-tag>
                            </div>
                            <div class="project-time" style="display: flex; justify-content: space-between; align-items: center;">
                                <span><el-icon><Clock /></el-icon> {{ formatTime(project.created_at) }}</span>
                                <el-button type="danger" size="small" text @click.stop="deleteProject(project)" :icon="Delete">
                                    删除
                                </el-button>
                            </div>
                        </div>
                    </el-card>
                </el-col>
            </el-row>

            <!-- 新建项目对话框 -->
            <el-dialog v-model="createDialogVisible" title="新建视频项目" width="600px" :close-on-click-modal="false">
                <el-form :model="createForm" label-width="100px">
                    <el-form-item label="视频主题" required>
                        <el-input v-model="createForm.topic" placeholder="请输入视频主题，如：AI智能手表评测" maxlength="100" show-word-limit></el-input>
                    </el-form-item>
                    <el-form-item label="视频时长">
                        <el-radio-group v-model="createForm.target_duration">
                            <el-radio-button :value="60">短视频 (60秒)</el-radio-button>
                            <el-radio-button :value="120">中等 (2分钟)</el-radio-button>
                            <el-radio-button :value="180">长视频 (3分钟)</el-radio-button>
                        </el-radio-group>
                    </el-form-item>
                    <el-form-item label="视频风格">
                        <el-select v-model="createForm.style" style="width: 100%">
                            <el-option label="营销推广" value="marketing"></el-option>
                            <el-option label="纪录片" value="documentary"></el-option>
                            <el-option label="叙事故事" value="narrative"></el-option>
                        </el-select>
                    </el-form-item>
                    <el-form-item label="产品卖点">
                        <el-input
                            v-model="createForm.selling_points"
                            type="textarea"
                            :rows="3"
                            placeholder="请输入产品卖点，如：AI健康监测/7天续航/IP68防水（可选）"
                            maxlength="500"
                            show-word-limit>
                        </el-input>
                    </el-form-item>
                    <el-form-item label="产品图片">
                        <el-upload
                            ref="uploadRef"
                            :auto-upload="false"
                            :file-list="createForm.productFiles"
                            :on-change="onFileChange"
                            :on-remove="onFileRemove"
                            :limit="5"
                            accept="image/*"
                            list-type="picture-card"
                            :on-exceed="() => ElMessage.warning('最多上传5张产品图')">
                            <el-icon><Plus /></el-icon>
                        </el-upload>
                        <div style="color: #909399; font-size: 12px; margin-top: 5px;">最多上传5张产品图（可选），用于产品展示镜头</div>
                    </el-form-item>
                </el-form>
                <template #footer>
                    <el-button @click="createDialogVisible = false" :disabled="creating">取消</el-button>
                    <el-button type="primary" @click="createProject" :loading="creating">
                        {{ creating ? '创建中（AI脚本生成中）...' : '确认创建' }}
                    </el-button>
                </template>
            </el-dialog>
        </div>
    `,

    data() {
        return {
            projects: [],
            loading: false,
            createDialogVisible: false,
            creating: false,
            createForm: {
                topic: '',
                target_duration: 60,
                style: 'marketing',
                selling_points: '',
                productFiles: []
            }
        }
    },

    async mounted() {
        await this.loadProjects();
    },

    methods: {
        async loadProjects() {
            this.loading = true;
            try {
                const response = await fetch('/api/projects');
                if (!response.ok) {
                    throw new Error('加载项目列表失败');
                }
                this.projects = await response.json();
                console.log('项目列表:', this.projects);
            } catch (error) {
                console.error('加载项目失败:', error);
                ElMessage.error('加载项目列表失败');
            } finally {
                this.loading = false;
            }
        },

        async refresh() {
            await this.loadProjects();
            ElMessage.success('刷新成功');
        },

        handleCreateCommand(command) {
            if (command === 'smart') {
                this.$emit('smart-create');
            } else {
                this.showCreateDialog();
            }
        },

        showCreateDialog() {
            this.createForm = {
                topic: '',
                target_duration: 60,
                style: 'marketing',
                selling_points: '',
                productFiles: []
            };
            this.createDialogVisible = true;
        },

        onFileChange(file, fileList) {
            this.createForm.productFiles = fileList;
        },

        onFileRemove(file, fileList) {
            this.createForm.productFiles = fileList;
        },

        async createProject() {
            if (!this.createForm.topic.trim()) {
                ElMessage.warning('请输入视频主题');
                return;
            }

            this.creating = true;
            try {
                // Step 1: 创建项目（含Gemini脚本生成）
                const response = await fetch('/api/projects/create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        topic: this.createForm.topic,
                        target_duration: this.createForm.target_duration,
                        style: this.createForm.style,
                        selling_points: this.createForm.selling_points || null
                    })
                });

                if (!response.ok) {
                    let err;
                    try { err = await response.json(); } catch(_) { err = {}; }
                    throw new Error(err.detail || '创建项目失败');
                }

                const result = await response.json();
                console.log('项目创建成功:', result);

                const projectId = result.data.project_id;

                // Step 2: 如果有产品图，上传
                if (this.createForm.productFiles.length > 0) {
                    try {
                        const formData = new FormData();
                        this.createForm.productFiles.forEach(f => {
                            formData.append('files', f.raw);
                        });

                        const uploadResp = await fetch(`/api/projects/${projectId}/upload-images`, {
                            method: 'POST',
                            body: formData
                        });

                        if (uploadResp.ok) {
                            const uploadResult = await uploadResp.json();
                            console.log('产品图上传成功:', uploadResult);
                        } else {
                            console.warn('产品图上传失败，但项目已创建');
                        }
                    } catch (uploadErr) {
                        console.warn('产品图上传异常:', uploadErr);
                    }
                }

                ElMessage.success(result.message || '项目创建成功');
                this.createDialogVisible = false;

                // Step 3: 直接进入脚本编辑页
                this.$emit('select-project', {
                    project_id: projectId,
                    title: result.data.title,
                    shot_count: result.data.shot_count,
                    total_duration: result.data.total_duration,
                    generation_stage: 'script'
                });

            } catch (error) {
                console.error('创建项目失败:', error);
                ElMessage.error('创建项目失败，请检查网络连接后重试');
            } finally {
                this.creating = false;
            }
        },

        async deleteProject(project) {
            try {
                await ElMessageBox.confirm(
                    `确定要删除项目「${project.title}」吗？此操作不可撤销。`,
                    '确认删除',
                    { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
                );
            } catch {
                return; // 用户取消
            }

            try {
                const response = await fetch(`/api/projects/${project.project_id}`, { method: 'DELETE' });
                if (!response.ok) throw new Error('删除失败');
                ElMessage.success('项目已删除');
                await this.loadProjects();
            } catch (error) {
                ElMessage.error('删除项目失败，请重试');
            }
        },

        stageLabel(stage) {
            const labels = {
                'script': '脚本阶段',
                'keyframes': '关键帧就绪',
                'videos': '视频就绪',
                'export': '已导出'
            };
            return labels[stage] || stage || '未知';
        },

        stageTagType(stage) {
            const types = { 'script': 'info', 'keyframes': 'warning', 'videos': 'success', 'export': 'success' };
            return types[stage] || 'info';
        },

        handleThumbnailError(e) {
            e.target.style.display = 'none';
        },

        formatTime(timestamp) {
            if (!timestamp) return '未知时间';
            const date = new Date(timestamp);
            const now = new Date();
            const diff = now - date;

            if (diff < 3600000) {
                const minutes = Math.floor(diff / 60000);
                return `${minutes}分钟前`;
            }
            if (diff < 86400000) {
                const hours = Math.floor(diff / 3600000);
                return `${hours}小时前`;
            }
            return date.toLocaleDateString('zh-CN', {
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        }
    }
});

// ==================== 智能脚本创作组件 ====================

app.component('script-creator-v2', {
    template: `
        <div class="script-creator-container">
            <div class="list-header">
                <el-button @click="$emit('back')" :icon="ArrowLeft">返回项目列表</el-button>
                <h2>智能脚本创作</h2>
                <el-steps :active="stepsActive" finish-status="success" simple style="max-width: 800px;">
                    <el-step title="产品信息"></el-step>
                    <el-step title="市场研究"></el-step>
                    <el-step title="选择方向"></el-step>
                    <el-step title="选择开场"></el-step>
                    <el-step title="脚本打磨"></el-step>
                </el-steps>
            </div>

            <!-- 步骤0: 产品输入 -->
            <div v-if="currentStep === 0" style="max-width: 660px; margin: 30px auto;">

                <!-- 模式切换 -->
                <div style="text-align: center; margin-bottom: 24px;">
                    <el-radio-group v-model="form.mode" size="large" @change="onModeChange">
                        <el-radio-button value="quick">⚡ 快速模式</el-radio-button>
                        <el-radio-button value="detailed">🤖 深度定制</el-radio-button>
                    </el-radio-group>
                    <div style="font-size: 13px; color: #909399; margin-top: 8px;">
                        {{ form.mode === 'quick' ? '填3项，秒出3个创意方向' : 'AI对话收集需求，自动匹配最适合的内容方法论' }}
                    </div>
                </div>

                <!-- ⚡ 快速模式 -->
                <el-card v-if="form.mode === 'quick'" shadow="always">
                    <template #header>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="font-size: 18px;">⚡</span>
                            <span style="font-weight: bold; font-size: 16px;">快速创作</span>
                            <el-tag type="success" size="small">推荐</el-tag>
                        </div>
                    </template>
                    <el-form label-width="72px" style="margin-top: 4px;">
                        <el-form-item label="产品" required>
                            <el-input v-model="form.product_name" placeholder="如：美白面霜、智能手表、蛋白粉" maxlength="50" size="large" @keyup.enter="startResearch" clearable></el-input>
                        </el-form-item>
                        <el-form-item label="品类">
                            <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                                <span v-for="ind in industryOptions" :key="ind.value"
                                    @click="form.industry = (form.industry === ind.value ? null : ind.value)"
                                    :style="{ display: 'inline-block', padding: '4px 14px', borderRadius: '16px', cursor: 'pointer', fontSize: '13px', border: '1px solid', borderColor: form.industry === ind.value ? '#409eff' : '#dcdfe6', background: form.industry === ind.value ? '#409eff' : '#fff', color: form.industry === ind.value ? '#fff' : '#606266', transition: 'all 0.2s', userSelect: 'none' }">
                                    {{ ind.label }}
                                </span>
                            </div>
                        </el-form-item>
                        <el-form-item label="时长">
                            <el-radio-group v-model="form.target_duration">
                                <el-radio-button :value="30">30秒</el-radio-button>
                                <el-radio-button :value="60">60秒</el-radio-button>
                                <el-radio-button :value="120">2分钟</el-radio-button>
                                <el-radio-button :value="180">3分钟</el-radio-button>
                            </el-radio-group>
                        </el-form-item>
                        <el-form-item>
                            <el-button type="primary" size="large" @click="startResearch" :disabled="!form.product_name.trim()" style="width: 100%; font-size: 15px;">
                                ⚡ 快速生成创意方向
                            </el-button>
                        </el-form-item>
                    </el-form>
                </el-card>

                <!-- 🤖 深度定制: AI对话收集 -->
                <el-card v-else shadow="always">
                    <template #header>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="font-size: 18px;">🤖</span>
                            <span style="font-weight: bold; font-size: 16px;">AI深度定制</span>
                            <el-tag type="warning" size="small">量身定制</el-tag>
                        </div>
                    </template>
                    <!-- 视频时长（在聊天外单独选） -->
                    <div style="margin-bottom: 14px; display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 13px; color: #606266; flex-shrink: 0;">视频时长：</span>
                        <el-radio-group v-model="form.target_duration" size="small">
                            <el-radio-button :value="30">30秒</el-radio-button>
                            <el-radio-button :value="60">60秒</el-radio-button>
                            <el-radio-button :value="120">2分钟</el-radio-button>
                            <el-radio-button :value="180">3分钟</el-radio-button>
                        </el-radio-group>
                    </div>
                    <!-- 聊天窗口 -->
                    <div ref="intakeChatBox" style="min-height: 240px; max-height: 400px; overflow-y: auto; padding: 14px; background: #f8f9fa; border-radius: 8px; margin-bottom: 12px;">
                        <div v-for="(msg, i) in intakeMessages" :key="i" style="margin-bottom: 14px;">
                            <div v-if="msg.role === 'ai'" style="display: flex; align-items: flex-start; gap: 10px;">
                                <div style="width: 30px; height: 30px; border-radius: 50%; background: linear-gradient(135deg, #409eff, #67c23a); display: flex; align-items: center; justify-content: center; color: white; font-size: 11px; font-weight: bold; flex-shrink: 0;">AI</div>
                                <div style="background: white; border: 1px solid #e4e7ed; border-radius: 2px 12px 12px 12px; padding: 10px 14px; max-width: 84%; font-size: 14px; color: #303133; line-height: 1.7; white-space: pre-line; box-shadow: 0 1px 4px rgba(0,0,0,0.06);">{{ msg.text }}</div>
                            </div>
                            <div v-else style="display: flex; justify-content: flex-end;">
                                <div style="background: #409eff; border-radius: 12px 2px 12px 12px; padding: 10px 14px; max-width: 84%; font-size: 14px; color: white; line-height: 1.7;">{{ msg.text }}</div>
                            </div>
                        </div>
                    </div>
                    <!-- 输入框 / 状态区 -->
                    <div v-if="intakeStep < 4" style="display: flex; gap: 8px;">
                        <el-input v-model="intakeInput" :placeholder="intakePlaceholder" @keyup.enter="submitIntakeAnswer" size="large" :disabled="intakeProcessing" clearable></el-input>
                        <el-button type="primary" @click="submitIntakeAnswer" :disabled="!intakeInput.trim() || intakeProcessing" size="large" style="flex-shrink: 0;">发送</el-button>
                    </div>
                    <div v-else-if="intakeStep === 4" style="text-align: center; padding: 12px 0;">
                        <el-icon class="is-loading" :size="28" style="color: #409eff;"><Loading /></el-icon>
                        <p style="color: #909399; margin-top: 8px; font-size: 13px;">AI正在分析需求，匹配最佳内容方法论...</p>
                    </div>
                    <div v-else-if="intakeStep === 5" style="text-align: center; padding: 8px 0;">
                        <el-button type="primary" size="large" @click="startResearch()" style="padding: 12px 40px; font-size: 15px;">
                            开始生成创意方向 →
                        </el-button>
                        <div style="margin-top: 8px;">
                            <el-button text type="info" @click="form.template_id = null; selectedTemplateInfo = null; startResearch()">不用此模板，自由发挥</el-button>
                        </div>
                    </div>
                </el-card>
            </div>

            <!-- 步骤1: 研究中 -->
            <div v-else-if="currentStep === 1" style="max-width: 500px; margin: 80px auto; text-align: center;">
                <el-icon class="is-loading" :size="60" style="color: #409eff;"><Loading /></el-icon>
                <h3 style="margin-top: 20px;">{{ researchStatus }}</h3>
                <el-progress :percentage="researchProgress" :stroke-width="10" style="margin-top: 20px;"></el-progress>
                <p style="color: #909399; margin-top: 15px;">{{ form.mode === 'quick' ? 'AI正在快速生成创意方向，请稍候...' : '正在为「' + form.product_name + '」进行市场调研和竞品分析...' }}</p>
            </div>

            <!-- 步骤2: 选择方向 -->
            <div v-else-if="currentStep === 2" style="max-width: 1100px; margin: 30px auto;">

                <!-- 模板来源标签 (Feature A) -->
                <div v-if="selectedTemplateInfo" style="margin-bottom: 16px; padding: 12px 18px; background: linear-gradient(135deg, #f0f9ff, #e6f4ff); border: 1px solid #bae0ff; border-radius: 10px; display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                    <span style="font-size: 16px;">✨</span>
                    <span style="font-size: 13px; color: #4a7fa5;">创意方向基于</span>
                    <strong style="font-size: 15px; color: #1677ff;">{{ selectedTemplateInfo.name }}</strong>
                    <el-tag type="primary" size="small" effect="light">{{ selectedTemplateInfo.source && selectedTemplateInfo.source.label }}</el-tag>
                    <span v-if="selectedTemplateInfo.source && selectedTemplateInfo.source.followers" style="font-size: 12px; color: #909399;">{{ selectedTemplateInfo.source.followers }}</span>
                    <el-button text type="info" size="small" @click="selectedTemplateInfo = null; form.template_id = null">不使用此模板</el-button>
                </div>

                <div style="margin-bottom: 20px;">
                    <h3>竞品洞察</h3>
                    <el-card shadow="never" style="background: #f5f7fa;">
                        <el-row :gutter="20">
                            <el-col :span="8">
                                <h4>成功模式</h4>
                                <el-tag v-for="p in (result.competitor_summary.winning_patterns || [])" :key="p" style="margin: 3px;" type="success">{{ p }}</el-tag>
                            </el-col>
                            <el-col :span="8">
                                <h4>开场策略</h4>
                                <el-tag v-for="h in (result.competitor_summary.hook_strategies || [])" :key="h" style="margin: 3px;" type="warning">{{ h }}</el-tag>
                            </el-col>
                            <el-col :span="8">
                                <h4>市场摘要</h4>
                                <p style="font-size: 13px; color: #606266;">{{ (result.market_summary.summary || '').substring(0, 200) }}</p>
                            </el-col>
                        </el-row>
                    </el-card>
                </div>

                <h3 style="margin-bottom: 15px;">选择创意方向</h3>
                <el-row :gutter="20">
                    <el-col :span="8" v-for="dir in result.directions" :key="dir.direction_id">
                        <el-card
                            shadow="hover"
                            class="direction-card"
                            :class="{ 'direction-selected': selectedDirection === dir.direction_id }"
                            @click="selectedDirection = dir.direction_id"
                            style="cursor: pointer; height: 100%;">
                            <template #header>
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span style="font-size: 18px; font-weight: bold;">{{ dir.name }}</span>
                                    <el-tag
                                        :type="dir.risk_level === 'safe' ? 'success' : dir.risk_level === 'moderate' ? 'warning' : 'danger'"
                                        size="small">
                                        {{ dir.risk_level === 'safe' ? '低风险' : dir.risk_level === 'moderate' ? '中等风险' : '高风险高回报' }}
                                    </el-tag>
                                </div>
                            </template>
                            <p style="color: #606266; margin-bottom: 12px;">{{ dir.description }}</p>
                            <div style="background: #f0f9ff; padding: 10px; border-radius: 6px; margin-bottom: 12px;">
                                <strong>开场钩子:</strong>
                                <p style="color: #409eff; margin: 5px 0 0;">{{ dir.hook }}</p>
                            </div>
                            <div style="margin-bottom: 12px;">
                                <strong>内容结构:</strong>
                                <div v-for="s in dir.structure_preview" :key="s" style="font-size: 13px; color: #909399; padding: 2px 0;">
                                    {{ s }}
                                </div>
                            </div>
                            <div v-if="dir.creative_techniques && dir.creative_techniques.length > 0">
                                <strong>创意手法:</strong>
                                <el-tag v-for="t in dir.creative_techniques" :key="t" size="small" type="danger" style="margin: 3px;">{{ t }}</el-tag>
                            </div>
                        </el-card>
                    </el-col>
                </el-row>

                <div style="text-align: center; margin-top: 30px;">
                    <el-button @click="currentStep = 0">重新输入</el-button>
                    <el-button type="primary" size="large" @click="selectDirection" :disabled="!selectedDirection" :loading="generating">
                        {{ generating ? '正在分析卖点和生成开场...' : '确认方向，选择开场' }}
                    </el-button>
                </div>
            </div>

            <!-- 步骤3: 选择开场Hook (NEW) -->
            <div v-else-if="currentStep === 3" style="max-width: 1100px; margin: 30px auto;">
                <!-- 卖点标签 -->
                <div style="margin-bottom: 20px;">
                    <h3>核心卖点</h3>
                    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                        <el-tag v-for="sp in sellingPoints" :key="sp" size="large" type="primary" effect="dark" style="font-size: 14px; padding: 8px 16px;">
                            {{ sp }}
                        </el-tag>
                    </div>
                </div>

                <h3 style="margin-bottom: 15px;">选择开场方式</h3>
                <p style="color: #909399; margin-bottom: 20px;">5种不同风格的开场，选择最适合你产品的一个</p>

                <el-row :gutter="16">
                    <el-col :span="12" v-for="hook in hookCandidates" :key="hook.hook_id" style="margin-bottom: 16px;">
                        <el-card
                            shadow="hover"
                            :class="{ 'direction-selected': selectedHook === hook.hook_id }"
                            @click="selectedHook = hook.hook_id"
                            style="cursor: pointer; height: 100%;">
                            <template #header>
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <el-tag :type="hookTagType(hook.style)" size="default" effect="dark">{{ hook.style }}</el-tag>
                                    <el-icon v-if="selectedHook === hook.hook_id" style="color: #67c23a; font-size: 20px;"><CircleCheck /></el-icon>
                                </div>
                            </template>
                            <div style="margin-bottom: 12px;">
                                <div style="font-size: 16px; font-weight: bold; color: #303133; line-height: 1.5;">
                                    "{{ hook.hook_text }}"
                                </div>
                            </div>
                            <div style="font-size: 12px; color: #909399; margin-bottom: 10px;">
                                {{ hook.visual_hint }}
                            </div>
                            <div style="background: #fdf6ec; padding: 8px 12px; border-radius: 6px; border-left: 3px solid #e6a23c;">
                                <span style="font-size: 12px; color: #e6a23c; font-weight: bold;">创作依据: </span>
                                <span style="font-size: 12px; color: #606266;">{{ hook.rationale }}</span>
                            </div>
                        </el-card>
                    </el-col>
                </el-row>

                <div style="text-align: center; margin-top: 30px;">
                    <el-button @click="currentStep = 2">返回选方向</el-button>
                    <el-button type="primary" size="large" @click="selectHook" :disabled="!selectedHook" :loading="generatingScript">
                        {{ generatingScript ? '正在生成脚本...' : '确认开场，生成脚本' }}
                    </el-button>
                </div>
            </div>

            <!-- 步骤4: 生成中 (NEW) -->
            <div v-else-if="currentStep === 4" style="max-width: 500px; margin: 80px auto; text-align: center;">
                <el-icon class="is-loading" :size="60" style="color: #67c23a;"><Loading /></el-icon>
                <h3 style="margin-top: 20px;">{{ generateStatus }}</h3>
                <el-progress :percentage="generateProgress" :stroke-width="10" status="success" style="margin-top: 20px;"></el-progress>
                <p style="color: #909399; margin-top: 15px;">AI正在分步骤精心打磨脚本...</p>
            </div>

            <!-- 步骤5: 脚本预览+打磨 -->
            <div v-else-if="currentStep === 5" style="max-width: 1200px; margin: 20px auto;">
                <!-- 质量自检卡片 -->
                <div v-if="qualityCheck" style="margin-bottom: 20px;">
                    <el-card shadow="never" :style="{ background: qualityCheck.issues.length === 0 ? '#f0f9eb' : '#fdf6ec', border: qualityCheck.issues.length === 0 ? '1px solid #e1f3d8' : '1px solid #faecd8' }">
                        <div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">
                            <div style="display: flex; align-items: center; gap: 6px;">
                                <el-icon v-if="qualityCheck.issues.length === 0" style="color: #67c23a; font-size: 20px;"><CircleCheck /></el-icon>
                                <el-icon v-else style="color: #e6a23c; font-size: 20px;"><Warning /></el-icon>
                                <strong>{{ qualityCheck.issues.length === 0 ? '质量自检通过' : '质量自检发现问题' }}</strong>
                            </div>
                            <el-tag :type="qualityCheck.word_duration_match ? 'success' : 'warning'" size="small">
                                字数/时长 {{ qualityCheck.word_duration_match ? '匹配' : '偏长' }}
                            </el-tag>
                            <el-tag type="success" size="small">
                                卖点覆盖 {{ (qualityCheck.selling_point_coverage || []).length }}/{{ sellingPoints.length }}
                            </el-tag>
                            <el-tag :type="qualityCheck.rhythm_score >= 0.7 ? 'success' : 'warning'" size="small">
                                节奏评分 {{ Math.round(qualityCheck.rhythm_score * 100) }}%
                            </el-tag>
                            <div v-if="qualityCheck.auto_fixes && qualityCheck.auto_fixes.length > 0" style="width: 100%; margin-top: 8px;">
                                <div v-for="fix in qualityCheck.auto_fixes" :key="fix" style="font-size: 12px; color: #909399; padding: 2px 0;">
                                    - {{ fix }}
                                </div>
                            </div>
                            <div v-if="qualityCheck.issues.length > 0" style="width: 100%; margin-top: 8px;">
                                <div v-for="issue in qualityCheck.issues" :key="issue" style="font-size: 12px; color: #e6a23c; padding: 2px 0;">
                                    - {{ issue }}
                                </div>
                            </div>
                        </div>
                    </el-card>
                </div>

                <el-row :gutter="20">
                    <!-- 左侧: 脚本预览 -->
                    <el-col :span="14">
                        <el-card>
                            <template #header>
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <h3 style="margin: 0;">脚本预览</h3>
                                    <div style="display: flex; align-items: center; gap: 10px;">
                                        <el-tag>{{ scriptShots.length }} 个镜头</el-tag>
                                        <el-switch v-model="showRationale" active-text="创作依据" inactive-text="" size="small"></el-switch>
                                    </div>
                                </div>
                            </template>
                            <div style="max-height: 65vh; overflow-y: auto;">
                                <div v-for="shot in scriptShots" :key="shot.id" style="padding: 12px; border-bottom: 1px solid #f0f0f0;">
                                    <div style="display: flex; gap: 12px; align-items: flex-start;">
                                        <div style="min-width: 50px; text-align: center;">
                                            <div style="font-size: 20px; font-weight: bold; color: #409eff;">#{{ shot.id }}</div>
                                            <el-tag size="small" style="margin-top: 4px;">{{ shot.duration }}s</el-tag>
                                        </div>
                                        <div style="flex: 1;">
                                            <div style="font-size: 12px; color: #909399; margin-bottom: 4px;">
                                                [{{ shot.shot_type }}] {{ shot.visual_description }}
                                            </div>
                                            <div style="font-size: 14px; color: #303133;">
                                                {{ shot.narration }}
                                            </div>
                                            <!-- 创作依据面板 -->
                                            <div v-if="showRationale && shot.rationale" style="margin-top: 6px; padding: 6px 10px; background: #fdf6ec; border-radius: 4px; border-left: 3px solid #e6a23c;">
                                                <span style="font-size: 11px; color: #e6a23c; font-weight: bold;">依据: </span>
                                                <span style="font-size: 11px; color: #909399;">{{ shot.rationale }}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </el-card>
                    </el-col>

                    <!-- 右侧: 聊天面板 -->
                    <el-col :span="10">
                        <el-card style="height: calc(65vh + 80px); display: flex; flex-direction: column;">
                            <template #header><h3 style="margin: 0;">对话打磨</h3></template>

                            <!-- 快捷指令 -->
                            <div style="margin-bottom: 10px; display: flex; flex-wrap: wrap; gap: 6px;">
                                <el-button size="small" @click="sendQuickMessage('开头太平淡了，换一个更吸引人的')">优化开头</el-button>
                                <el-button size="small" @click="sendQuickMessage('结尾号召行动不够有力')">优化结尾</el-button>
                                <el-button size="small" @click="sendQuickMessage('口播文案太书面化，改成更口语化的')">口语化</el-button>
                                <el-button size="small" @click="sendQuickMessage('增加紧迫感和促销元素')">增加紧迫感</el-button>
                            </div>

                            <!-- 聊天记录 -->
                            <div ref="chatBox" style="flex: 1; overflow-y: auto; margin-bottom: 10px; padding: 10px; background: #fafafa; border-radius: 6px;">
                                <div v-for="(msg, i) in chatMessages" :key="i" style="margin-bottom: 12px;">
                                    <div v-if="msg.role === 'user'" style="text-align: right;">
                                        <span style="background: #409eff; color: white; padding: 8px 12px; border-radius: 12px 12px 0 12px; display: inline-block; max-width: 80%;">
                                            {{ msg.content }}
                                        </span>
                                    </div>
                                    <div v-else>
                                        <span style="background: #f0f0f0; padding: 8px 12px; border-radius: 12px 12px 12px 0; display: inline-block; max-width: 80%;">
                                            {{ msg.content }}
                                        </span>
                                        <div v-if="msg.changes && msg.changes.length > 0" style="margin-top: 4px;">
                                            <el-tag v-for="c in msg.changes" :key="c" size="small" type="info" style="margin: 2px;">{{ c }}</el-tag>
                                        </div>
                                    </div>
                                </div>
                                <div v-if="chatLoading" style="text-align: left;">
                                    <span style="background: #f0f0f0; padding: 8px 12px; border-radius: 12px; display: inline-block;">
                                        <el-icon class="is-loading"><Loading /></el-icon> 思考中...
                                    </span>
                                </div>
                            </div>

                            <!-- 输入框 -->
                            <div style="display: flex; gap: 8px;">
                                <el-input
                                    v-model="chatInput"
                                    placeholder="告诉AI你想怎么改..."
                                    @keyup.enter="sendChatMessage"
                                    :disabled="chatLoading">
                                </el-input>
                                <el-button type="primary" @click="sendChatMessage" :disabled="!chatInput.trim() || chatLoading">发送</el-button>
                            </div>
                        </el-card>

                        <!-- 底部操作 -->
                        <div style="margin-top: 15px; display: flex; justify-content: center; gap: 15px;">
                            <el-button @click="currentStep = 3">返回选开场</el-button>
                            <el-button type="success" size="large" @click="lockAndProceed" :loading="locking">
                                确认脚本，进入关键帧
                            </el-button>
                        </div>
                    </el-col>
                </el-row>
            </div>

            <!-- 品牌档案对话框 -->
            <el-dialog v-model="showBrandDialog" title="新建品牌档案" width="500px">
                <el-form :model="brandForm" label-width="90px">
                    <el-form-item label="品牌名称" required>
                        <el-input v-model="brandForm.brand_name" placeholder="如: 花西子"></el-input>
                    </el-form-item>
                    <el-form-item label="品牌调性">
                        <el-input v-model="brandForm.brand_tone" placeholder="如: 高端、国风、年轻活力"></el-input>
                    </el-form-item>
                    <el-form-item label="目标受众">
                        <el-input v-model="brandForm.target_audience" placeholder="如: 20-35岁女性"></el-input>
                    </el-form-item>
                    <el-form-item label="视觉风格">
                        <el-input v-model="brandForm.visual_style" placeholder="如: 简约白底、中国风"></el-input>
                    </el-form-item>
                    <el-form-item label="禁用词">
                        <el-input v-model="brandForm.forbidden_words_text" placeholder="多个用逗号分隔，如: 最好,第一,绝对"></el-input>
                    </el-form-item>
                </el-form>
                <template #footer>
                    <el-button @click="showBrandDialog = false">取消</el-button>
                    <el-button type="primary" @click="createBrandProfile" :loading="creatingBrand">保存</el-button>
                </template>
            </el-dialog>
        </div>
    `,

    data() {
        return {
            currentStep: 0,
            form: {
                product_name: '',
                industry: null,
                target_duration: 60,
                mode: 'quick',
                product_detail: '',
                template_id: null
            },
            industryOptions: [
                { label: '美妆护肤', value: '美妆护肤' },
                { label: '数码科技', value: '数码科技' },
                { label: '食品饮料', value: '食品饮料' },
                { label: '服装配饰', value: '服装配饰' },
                { label: '家居生活', value: '家居生活' },
                { label: '母婴', value: '母婴用品' },
                { label: '健康保健', value: '健康保健' },
                { label: '教育', value: '教育培训' },
            ],
            // 深度定制对话收集
            intakeMessages: [],
            intakeStep: 0,
            intakeInput: '',
            intakeProcessing: false,
            intakeAnswers: { product_name: '', problem_user: '', differentiation: '' },
            matchedTemplates: [],
            matchingTemplates: false,
            selectedTemplateInfo: null,   // 已选中的模板完整信息
            brandProfiles: [],
            showBrandDialog: false,
            creatingBrand: false,
            brandForm: {
                brand_name: '',
                brand_tone: '',
                target_audience: '',
                visual_style: '',
                forbidden_words_text: ''
            },
            // 研究阶段
            researchStatus: '搜索同行爆款视频...',
            researchProgress: 0,
            // 方向选择
            result: { competitor_summary: {}, market_summary: {}, directions: [] },
            sessionId: '',
            selectedDirection: null,
            generating: false,
            // Hook选择 (NEW)
            hookCandidates: [],
            sellingPoints: [],
            selectedHook: null,
            generatingScript: false,
            generateStatus: '创建镜头结构...',
            generateProgress: 0,
            // 脚本打磨
            projectId: '',
            scriptShots: [],
            qualityCheck: null,
            showRationale: true,
            chatMessages: [],
            chatInput: '',
            chatLoading: false,
            locking: false
        }
    },

    computed: {
        stepsActive() {
            if (this.currentStep <= 3) return this.currentStep;
            if (this.currentStep === 4) return 3;
            return 4;
        },
        intakePlaceholder() {
            const map = {
                1: '输入产品名称，如：轻奢美白精华、智能跑步机...',
                2: '描述产品解决的问题 + 目标用户是谁...',
                3: '描述核心差异化优势，越具体越好...'
            };
            return map[this.intakeStep] || '请输入...';
        }
    },

    async mounted() {
        await this.loadBrandProfiles();
    },

    methods: {
        async loadBrandProfiles() {
            try {
                const resp = await fetch('/api/brand-profiles/');
                if (resp.ok) {
                    this.brandProfiles = await resp.json();
                }
            } catch (e) {
                console.error('加载品牌档案失败:', e);
            }
        },

        onModeChange(mode) {
            if (mode === 'detailed') {
                this.initIntake();
            } else {
                // 切回快速模式时重置
                this.form.product_name = '';
                this.form.product_detail = '';
                this.form.template_id = null;
            }
        },

        initIntake() {
            this.intakeMessages = [
                { role: 'ai', text: '你好！我是你的脚本创意顾问 👋\n\n为了给你量身定制最合适的内容方向，我需要了解几个情况。先告诉我，你想为哪款产品创作视频？' }
            ];
            this.intakeStep = 1;
            this.intakeInput = '';
            this.intakeAnswers = { product_name: '', problem_user: '', differentiation: '' };
            this.$nextTick(() => { this.scrollIntakeChat(); });
        },

        async submitIntakeAnswer() {
            const answer = this.intakeInput.trim();
            if (!answer || this.intakeProcessing) return;

            this.intakeMessages.push({ role: 'user', text: answer });
            this.intakeInput = '';
            this.$nextTick(() => { this.scrollIntakeChat(); });

            if (this.intakeStep === 1) {
                this.intakeAnswers.product_name = answer;
                this.form.product_name = answer;
                setTimeout(() => {
                    this.intakeMessages.push({ role: 'ai', text: '好的！「' + answer + '」👍\n\n这款产品主要解决什么问题？目标用户是哪类人群？\n（比如：帮助熬夜党改善肤色暗沉，主要面向25-35岁职场女性）' });
                    this.intakeStep = 2;
                    this.$nextTick(() => { this.scrollIntakeChat(); });
                }, 500);

            } else if (this.intakeStep === 2) {
                this.intakeAnswers.problem_user = answer;
                setTimeout(() => {
                    this.intakeMessages.push({ role: 'ai', text: '明白了 ✅\n\n最后一个问题——和同类产品比，你们最大的亮点或差异是什么？\n（比如：独家专利成分 / 价格只有竞品一半 / 某明星同款）' });
                    this.intakeStep = 3;
                    this.$nextTick(() => { this.scrollIntakeChat(); });
                }, 500);

            } else if (this.intakeStep === 3) {
                this.intakeAnswers.differentiation = answer;
                this.intakeStep = 4;
                this.intakeProcessing = true;

                setTimeout(() => {
                    this.intakeMessages.push({ role: 'ai', text: '收到！正在为你分析最适合的内容方法论...' });
                    this.$nextTick(() => { this.scrollIntakeChat(); });
                }, 400);

                // 组装 product_detail
                this.form.product_detail = `解决问题与目标用户：${this.intakeAnswers.problem_user}；核心差异化优势：${this.intakeAnswers.differentiation}`;

                // 自动匹配模板
                try {
                    const params = new URLSearchParams({ product_name: this.form.product_name, top_k: 1 });
                    if (this.form.product_detail) params.append('product_detail', this.form.product_detail);
                    const resp = await fetch(`/api/templates/match?${params.toString()}`, { method: 'POST' });
                    if (resp.ok) {
                        const data = await resp.json();
                        const matches = data.matched_templates || [];
                        if (matches.length > 0) {
                            const best = matches[0];
                            this.form.template_id = best.template_id;
                            this.selectedTemplateInfo = best;

                            // AI 宣布匹配结果
                            const src = best.source || {};
                            const announceText = `✅ 分析完成！\n\n我为「${this.form.product_name}」匹配了最适合的内容方法论：\n\n📌 ${best.name}\n来源：${src.label || src.name}\n${src.bio ? '「' + src.bio.substring(0, 60) + '」' : ''}\n\n核心策略：${best.core_strategy}\n\n${best.match_reason || ''}`;
                            setTimeout(() => {
                                this.intakeMessages.push({ role: 'ai', text: announceText });
                                this.intakeStep = 5;  // 等待用户确认
                                this.intakeProcessing = false;
                                this.$nextTick(() => { this.scrollIntakeChat(); });
                            }, 800);
                            return;
                        }
                    }
                } catch (e) {
                    console.warn('模板匹配失败，使用自由模式:', e);
                }

                // 无模板匹配时直接开始
                this.intakeProcessing = false;
                await this.startResearch();
            }
        },

        scrollIntakeChat() {
            if (this.$refs.intakeChatBox) {
                this.$refs.intakeChatBox.scrollTop = this.$refs.intakeChatBox.scrollHeight;
            }
        },

        async createBrandProfile() {
            if (!this.brandForm.brand_name.trim()) {
                ElMessage.warning('请输入品牌名称');
                return;
            }
            this.creatingBrand = true;
            try {
                const resp = await fetch('/api/brand-profiles/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        brand_name: this.brandForm.brand_name,
                        brand_tone: this.brandForm.brand_tone,
                        target_audience: this.brandForm.target_audience,
                        visual_style: this.brandForm.visual_style,
                        forbidden_words: this.brandForm.forbidden_words_text
                            ? this.brandForm.forbidden_words_text.split(',').map(s => s.trim()).filter(Boolean)
                            : []
                    })
                });
                if (resp.ok) {
                    ElMessage.success('品牌档案创建成功');
                    this.showBrandDialog = false;
                    await this.loadBrandProfiles();
                    const data = await resp.json();
                    if (data.data) this.form.brand_profile_id = data.data.profile_id;
                } else {
                    ElMessage.error('创建失败');
                }
            } catch (e) {
                ElMessage.error('创建品牌档案失败');
            } finally {
                this.creatingBrand = false;
            }
        },

        async startResearch() {
            if (!this.form.product_name.trim()) {
                ElMessage.warning('请输入产品名称');
                return;
            }
            this.currentStep = 1;
            this.researchProgress = 0;
            this.researchStatus = '搜索同行爆款视频...';

            // 模拟进度（快速模式更快）
            const isQuick = this.form.mode === 'quick';
            this._researchTimer = setInterval(() => {
                if (isQuick) {
                    if (this.researchProgress < 80) {
                        this.researchProgress += 10;
                        this.researchStatus = 'AI快速生成创意方向...';
                    }
                } else {
                    if (this.researchProgress < 30) {
                        this.researchProgress += 2;
                        this.researchStatus = '搜索同行爆款视频...';
                    } else if (this.researchProgress < 60) {
                        this.researchProgress += 2;
                        this.researchStatus = '分析市场情报...';
                    } else if (this.researchProgress < 85) {
                        this.researchProgress += 1;
                        this.researchStatus = '生成创意方向...';
                    }
                }
            }, 500);

            try {
                const resp = await fetch('/api/script/smart-create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        product_name: this.form.product_name,
                        industry: this.form.industry || null,
                        target_duration: this.form.target_duration,
                        mode: this.form.mode,
                        product_detail: this.form.product_detail || null,
                        template_id: this.form.template_id || null
                    })
                });

                clearInterval(this._researchTimer);

                if (!resp.ok) {
                    let err;
                    try { err = await resp.json(); } catch(_) { err = {}; }
                    throw new Error(err.detail || '研究失败');
                }

                this.result = await resp.json();
                this.sessionId = this.result.session_id;
                this.researchProgress = 100;
                this.researchStatus = '研究完成!';

                setTimeout(() => {
                    this.currentStep = 2;
                }, 500);

            } catch (e) {
                clearInterval(this._researchTimer);
                console.error('研究失败:', e);
                ElMessage.error('市场研究失败: ' + e.message);
                this.currentStep = 0;
            }
        },

        async selectDirection() {
            if (!this.selectedDirection) return;
            this.generating = true;

            try {
                const resp = await fetch(`/api/script/${this.sessionId}/select`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ direction_id: this.selectedDirection })
                });

                if (!resp.ok) {
                    let err;
                    try { err = await resp.json(); } catch(_) { err = {}; }
                    throw new Error(err.detail || '生成Hook失败');
                }

                const data = await resp.json();
                this.hookCandidates = data.data.hooks || [];
                this.sellingPoints = data.data.selling_points || [];

                this.currentStep = 3;
                // M15: 重置selectedHook，避免残留上次选择
                this.selectedHook = null;
                ElMessage.success('已生成5个开场方案，请选择！');

            } catch (e) {
                console.error('选择方向失败:', e);
                ElMessage.error('生成开场失败: ' + e.message);
            } finally {
                this.generating = false;
            }
        },

        async selectHook() {
            if (!this.selectedHook) return;
            this.generatingScript = true;
            this.currentStep = 4;
            this.generateProgress = 0;
            this.generateStatus = '创建镜头结构...';

            // 模拟多步进度
            this._generateTimer = setInterval(() => {
                if (this.generateProgress < 20) {
                    this.generateProgress += 3;
                    this.generateStatus = '创建镜头结构...';
                } else if (this.generateProgress < 50) {
                    this.generateProgress += 2;
                    this.generateStatus = '生成主体内容，覆盖核心卖点...';
                } else if (this.generateProgress < 75) {
                    this.generateProgress += 2;
                    this.generateStatus = '生成结尾，与开场呼应...';
                } else if (this.generateProgress < 90) {
                    this.generateProgress += 1;
                    this.generateStatus = '质量自检与自动优化...';
                }
            }, 500);

            try {
                const resp = await fetch(`/api/script/${this.sessionId}/select-hook`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ hook_id: this.selectedHook })
                });

                clearInterval(this._generateTimer);

                if (!resp.ok) {
                    let err;
                    try { err = await resp.json(); } catch(_) { err = {}; }
                    throw new Error(err.detail || '生成失败');
                }

                const data = await resp.json();
                this.projectId = data.data.project_id;
                this.scriptShots = data.data.shots || [];
                this.qualityCheck = data.data.quality_check || null;
                // M12: ensure shots is always an array
                if (data.data.selling_points) {
                    this.sellingPoints = data.data.selling_points;
                }

                this.generateProgress = 100;
                this.generateStatus = '脚本生成完成!';

                this.chatMessages = [{
                    role: 'assistant',
                    content: '脚本已生成！每个镜头都有创作依据。你可以告诉我想修改的地方，比如"开头不够吸引人"、"加入用户痛点"、"结尾增加紧迫感"等。'
                }];

                setTimeout(() => {
                    this.currentStep = 5;
                    ElMessage.success('脚本生成成功！');
                }, 500);

            } catch (e) {
                clearInterval(this._generateTimer);
                console.error('生成脚本失败:', e);
                ElMessage.error('脚本生成失败: ' + e.message);
                this.currentStep = 3;  // 返回Hook选择
            } finally {
                this.generatingScript = false;
            }
        },

        hookTagType(style) {
            const map = {
                '悬念型': '',
                '痛点型': 'danger',
                '数据型': 'success',
                '反常识型': 'warning',
                '场景代入型': 'info'
            };
            return map[style] || '';
        },

        async matchTemplates() {
            if (!this.form.product_name.trim()) {
                ElMessage.warning('请先输入产品名称');
                return;
            }
            this.matchingTemplates = true;
            try {
                const params = new URLSearchParams({ product_name: this.form.product_name, top_k: 3 });
                if (this.form.industry) params.append('industry', this.form.industry);
                if (this.form.product_detail) params.append('product_detail', this.form.product_detail);
                const resp = await fetch(`/api/templates/match?${params.toString()}`, { method: 'POST' });
                if (!resp.ok) throw new Error('匹配失败');
                const data = await resp.json();
                this.matchedTemplates = data.matched_templates || [];
                if (this.matchedTemplates.length > 0) {
                    ElMessage.success(`已为您匹配 ${this.matchedTemplates.length} 个最适合的模板`);
                } else {
                    ElMessage.info('未找到合适模板，将使用自由发挥模式');
                }
            } catch (e) {
                console.error('模板匹配失败:', e);
                ElMessage.error('模板匹配失败: ' + e.message);
            } finally {
                this.matchingTemplates = false;
            }
        },

        selectTemplate(tpl) {
            if (this.form.template_id === tpl.template_id) {
                this.form.template_id = null;
                ElMessage.info('已取消模板选择');
            } else {
                this.form.template_id = tpl.template_id;
                ElMessage.success(`已选择「${tpl.name}」模板`);
            }
        },

        async sendQuickMessage(msg) {
            this.chatInput = msg;
            await this.sendChatMessage();
        },

        async sendChatMessage() {
            const msg = this.chatInput.trim();
            if (!msg || this.chatLoading) return;

            this.chatMessages.push({ role: 'user', content: msg });
            this.chatInput = '';
            this.chatLoading = true;

            this.$nextTick(() => {
                if (this.$refs.chatBox) {
                    this.$refs.chatBox.scrollTop = this.$refs.chatBox.scrollHeight;
                }
            });

            try {
                const chatHistory = this.chatMessages
                    .filter(m => m.role === 'user' || m.role === 'assistant')
                    .map(m => ({ role: m.role, content: m.content }));

                const resp = await fetch(`/api/script/${this.projectId}/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: msg,
                        chat_history: chatHistory
                    })
                });

                if (!resp.ok) throw new Error('修改失败');

                const data = await resp.json();
                this.chatMessages.push({
                    role: 'assistant',
                    content: data.ai_response,
                    changes: data.changes_made
                });

                if (data.updated_shots && data.updated_shots.length > 0) {
                    this.scriptShots = data.updated_shots;
                }

            } catch (e) {
                this.chatMessages.push({
                    role: 'assistant',
                    content: '抱歉，修改暂时失败，请稍后再试'
                });
            } finally {
                this.chatLoading = false;
                this.$nextTick(() => {
                    if (this.$refs.chatBox) {
                        this.$refs.chatBox.scrollTop = this.$refs.chatBox.scrollHeight;
                    }
                });
            }
        },

        async lockAndProceed() {
            this.locking = true;
            try {
                const resp = await fetch(`/api/script/${this.projectId}/lock`, {
                    method: 'POST'
                });
                if (!resp.ok) throw new Error('锁定失败');

                ElMessage.success('脚本已锁定，即将进入关键帧生成');

                // 跳转到关键帧视图
                this.$emit('done', {
                    project_id: this.projectId,
                    title: this.form.product_name,
                    shot_count: this.scriptShots.length,
                    total_duration: this.scriptShots.reduce((sum, s) => sum + (s.duration || 5), 0),
                    generation_stage: 'script'
                });

            } catch (e) {
                ElMessage.error('锁定脚本失败');
            } finally {
                this.locking = false;
            }
        }
    },

    beforeUnmount() {
        // C8: 清理可能泄漏的定时器
        if (this._researchTimer) clearInterval(this._researchTimer);
        if (this._generateTimer) clearInterval(this._generateTimer);
    }
});

// ==================== 脚本编辑器组件 ====================

app.component('script-editor', {
    template: `
        <div class="script-editor-container">
            <div class="list-header">
                <el-button @click="$emit('back')" :icon="ArrowLeft">返回项目列表</el-button>
                <h2>{{ project.title || '脚本编辑' }} - 脚本审核</h2>
                <div>
                    <el-tag type="info">共 {{ shots.length }} 个镜头</el-tag>
                </div>
            </div>

            <div v-if="loading" style="text-align: center; padding: 50px;">
                <el-icon class="is-loading" :size="50"><Loading /></el-icon>
                <p>加载脚本中...</p>
            </div>

            <div v-else>
                <!-- 产品图预览 -->
                <div v-if="productImages.length > 0" style="margin-bottom: 20px; padding: 15px; background: #f5f7fa; border-radius: 8px;">
                    <h4 style="margin: 0 0 10px 0;">已上传的产品图 ({{ productImages.length }}张)</h4>
                    <div style="display: flex; gap: 10px;">
                        <img v-for="(img, i) in productImages" :key="i" :src="img"
                             style="width: 80px; height: 80px; object-fit: cover; border-radius: 6px; border: 1px solid #ddd;" />
                    </div>
                </div>

                <!-- 按幕分组显示 -->
                <div v-for="actGroup in groupedShots" :key="actGroup.act" style="margin-bottom: 30px;">
                    <h3 style="margin-bottom: 15px; padding: 8px 15px; background: linear-gradient(135deg, #409eff22, #67c23a22); border-radius: 6px;">
                        {{ actLabel(actGroup.act) }} ({{ actGroup.shots.length }}个镜头)
                    </h3>

                    <el-card v-for="shot in actGroup.shots" :key="shot.shot_id" shadow="hover"
                             style="margin-bottom: 15px;">
                        <div style="display: flex; align-items: flex-start; gap: 15px;">
                            <!-- 镜头编号和类型 -->
                            <div style="min-width: 80px; text-align: center;">
                                <div style="font-size: 24px; font-weight: bold; color: #409eff;">
                                    #{{ shot.shot_id }}
                                </div>
                                <el-tag :type="shotTypeColor(shot.shot_type)" size="small" style="margin-top: 5px;">
                                    {{ shotTypeLabel(shot.shot_type) }}
                                </el-tag>
                                <div style="margin-top: 5px; color: #909399; font-size: 12px;">
                                    {{ shot.duration }}秒
                                </div>
                                <el-tag v-if="shot.use_product_image" type="warning" size="small" style="margin-top: 5px;">
                                    产品图
                                </el-tag>
                            </div>

                            <!-- 内容编辑区 -->
                            <div style="flex: 1;">
                                <div style="margin-bottom: 10px;">
                                    <label style="font-weight: bold; color: #303133; display: block; margin-bottom: 5px;">
                                        画面描述 (英文，用于AI生图)
                                    </label>
                                    <el-input
                                        v-model="shot.visual_description"
                                        type="textarea"
                                        :rows="3"
                                        placeholder="英文画面描述..."
                                        @change="markDirty">
                                    </el-input>
                                </div>
                                <div>
                                    <label style="font-weight: bold; color: #303133; display: block; margin-bottom: 5px;">
                                        口播文案 (中文)
                                    </label>
                                    <el-input
                                        v-model="shot.narration"
                                        type="textarea"
                                        :rows="2"
                                        placeholder="中文口播文案..."
                                        @change="markDirty">
                                    </el-input>
                                </div>
                            </div>
                        </div>
                    </el-card>
                </div>

                <!-- 底部操作栏 -->
                <div style="position: sticky; bottom: 0; background: white; padding: 15px 0; border-top: 1px solid #eee; display: flex; justify-content: center; gap: 20px; z-index: 10;">
                    <el-button size="large" @click="$emit('back')">
                        返回修改
                    </el-button>
                    <el-button size="large" @click="saveScript" :loading="saving" :disabled="!isDirty">
                        保存修改
                    </el-button>
                    <el-button size="large" type="primary" @click="confirmAndGenerate" :loading="generating">
                        确认脚本，开始生成关键帧
                    </el-button>
                </div>
            </div>
        </div>
    `,

    props: ['project'],

    data() {
        return {
            loading: false,
            saving: false,
            generating: false,
            isDirty: false,
            shots: [],
            productImages: [],
            autosaveTimer: null
        }
    },

    computed: {
        groupedShots() {
            const groups = {};
            const order = ['act1', 'hook', 'act2', 'main', 'act3', 'climax'];
            this.shots.forEach(shot => {
                const act = shot.act_type || 'main';
                if (!groups[act]) {
                    groups[act] = { act, shots: [] };
                }
                groups[act].shots.push(shot);
            });
            // 按 hook -> main -> climax 排序
            const result = [];
            order.forEach(act => {
                if (groups[act]) result.push(groups[act]);
            });
            // 追加其他不在order中的
            Object.keys(groups).forEach(act => {
                if (!order.includes(act)) result.push(groups[act]);
            });
            return result;
        }
    },

    async mounted() {
        await this.loadScript();
    },

    methods: {
        async loadScript() {
            this.loading = true;
            try {
                const response = await fetch(`/api/projects/${this.project.project_id}/script`);
                if (!response.ok) throw new Error('加载脚本失败');

                const data = await response.json();
                this.shots = data.shots || [];
                this.productImages = data.product_images || [];
                console.log('脚本数据:', data);
            } catch (error) {
                console.error('加载脚本失败:', error);
                ElMessage.error('加载脚本失败: ' + error.message);
            } finally {
                this.loading = false;
            }
        },

        markDirty() {
            this.isDirty = true;
            // 自动保存：30秒无操作后自动保存
            if (this.autosaveTimer) clearTimeout(this.autosaveTimer);
            this.autosaveTimer = setTimeout(() => {
                if (this.isDirty && !this.saving) {
                    this.saveScript(true);
                }
            }, 30000);
        },

        async saveScript(silent = false) {
            this.saving = true;
            try {
                const response = await fetch(`/api/projects/${this.project.project_id}/script`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.shots)
                });

                if (!response.ok) throw new Error('保存脚本失败');

                this.isDirty = false;
                if (!silent) ElMessage.success('脚本已保存');
                else console.log('脚本自动保存成功');
            } catch (error) {
                console.error('保存脚本失败:', error);
                if (!silent) ElMessage.error('保存失败，请检查网络连接后重试');
            } finally {
                this.saving = false;
            }
        },

        async confirmAndGenerate() {
            this.generating = true;
            try {
                // 1. 先保存脚本
                if (this.isDirty) {
                    const saveResp = await fetch(`/api/projects/${this.project.project_id}/script`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(this.shots)
                    });
                    if (!saveResp.ok) throw new Error('保存脚本失败');
                    this.isDirty = false;
                }

                // 2. 调用生成关键帧
                const config = {
                    model: 'flux-pro',
                    quality: 'high',
                    aspect_ratio: '16:9',
                    optimize_prompt: true
                };

                const response = await fetch(`/api/projects/${this.project.project_id}/generate-keyframes`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                });

                if (!response.ok) throw new Error('创建关键帧生成任务失败');

                const task = await response.json();
                console.log('关键帧生成任务:', task);

                ElMessage.success(`开始生成关键帧，预估成本: ¥${task.estimated_cost.toFixed(2)}`);

                // 3. 跳转到关键帧视图
                this.$emit('go-keyframes');

            } catch (error) {
                console.error('生成关键帧失败:', error);
                ElMessage.error('生成关键帧失败，请稍后重试');
            } finally {
                this.generating = false;
            }
        },

        actLabel(act) {
            const labels = {
                'act1': '第一幕 - 开场吸引',
                'hook': '第一幕 - 开场吸引',
                'act2': '第二幕 - 主体内容',
                'main': '第二幕 - 主体内容',
                'act3': '第三幕 - 高潮结尾',
                'climax': '第三幕 - 高潮结尾'
            };
            return labels[act] || act;
        },

        shotTypeLabel(type) {
            const labels = {
                'opening': '开场',
                'talking_head': '讲解',
                'product': '产品展示',
                'hands_on': '上手演示',
                'broll': '空镜头',
                'comparison': '对比',
                'closing': '结尾'
            };
            return labels[type] || type;
        },

        shotTypeColor(type) {
            const colors = {
                'opening': 'danger',
                'talking_head': '',
                'product': 'warning',
                'hands_on': 'warning',
                'broll': 'info',
                'comparison': 'success',
                'closing': 'danger'
            };
            return colors[type] || 'info';
        }
    },

    beforeUnmount() {
        if (this.autosaveTimer) {
            clearTimeout(this.autosaveTimer);
            // 离开前自动保存未保存的修改
            if (this.isDirty) this.saveScript(true);
        }
    }
});

// ==================== 关键帧九宫格组件 ====================

app.component('keyframe-grid', {
    template: `
        <el-container class="keyframe-container">
            <!-- 顶部工具栏 -->
            <el-header class="keyframe-header" height="auto">
                <div class="header-top">
                    <el-button @click="$emit('back')" :icon="ArrowLeft">返回项目列表</el-button>
                    <h2>{{ project.title }} - 关键帧预览</h2>
                    <div class="header-actions">
                        <el-button v-if="generating" type="danger" @click="cancelGeneration">
                            <el-icon><Close /></el-icon> 取消生成
                        </el-button>
                        <el-button v-else-if="!hasKeyframes" type="primary" @click="generateKeyframes" :loading="generating">
                            <el-icon><Picture /></el-icon> 生成关键帧
                        </el-button>
                        <template v-else>
                            <el-button type="primary" @click="generateKeyframes">
                                <el-icon><Refresh /></el-icon> 重新生成全部
                            </el-button>
                            <el-button type="success" @click="approveAll" v-if="approvedCount < keyframes.length">
                                <el-icon><Check /></el-icon> 全部批准
                            </el-button>
                            <el-button type="success" @click="startImageToVideo" :disabled="!allKeyframesApproved">
                                <el-icon><VideoCamera /></el-icon> 生成视频
                            </el-button>
                        </template>
                    </div>
                </div>
                <div class="header-stats">
                    <el-tag type="info">{{ keyframes.length }} 个分镜</el-tag>
                    <el-tag type="success">{{ approvedCount }}/{{ keyframes.length }} 已批准</el-tag>
                    <el-tag type="warning">预估成本: ¥{{ estimatedCost.toFixed(2) }}</el-tag>
                    <el-progress v-if="generating" :percentage="Math.round(progress * 100)" :status="progressStatus"></el-progress>
                </div>
            </el-header>

            <!-- 九宫格内容 -->
            <el-main class="keyframe-grid-main">
                <div v-if="loading" class="loading-container">
                    <el-icon class="is-loading" :size="50"><Loading /></el-icon>
                    <p>加载关键帧中...</p>
                </div>

                <el-empty v-else-if="keyframes.length === 0" description="还没有生成关键帧">
                    <el-button type="primary" @click="generateKeyframes">开始生成关键帧</el-button>
                </el-empty>

                <div v-else class="keyframe-grid">
                    <el-card
                        v-for="(kf, index) in keyframes"
                        :key="kf.shot_id"
                        class="keyframe-card"
                        :class="{ 'approved': kf.status === 'approved' }"
                        shadow="hover"
                        @click="selectKeyframe(kf)">

                        <!-- 分镜编号 -->
                        <div class="keyframe-number">{{ index + 1 }}</div>

                        <!-- 状态标签 -->
                        <el-tag
                            v-if="kf.status === 'generating'"
                            class="keyframe-status"
                            type="warning"
                            size="small">
                            生成中...
                        </el-tag>
                        <el-tag
                            v-else-if="kf.status === 'approved'"
                            class="keyframe-status"
                            type="success"
                            size="small">
                            已批准
                        </el-tag>

                        <!-- 关键帧图片 -->
                        <div class="keyframe-image">
                            <img
                                v-if="getSelectedImageUrl(kf)"
                                :src="getSelectedImageUrl(kf)"
                                @error="handleImageError"
                                :alt="'Shot ' + kf.shot_id" />
                            <div v-else class="keyframe-placeholder">
                                <el-icon :size="40"><Picture /></el-icon>
                                <p>{{ kf.status === 'failed' ? '生成失败' : '待生成' }}</p>
                            </div>
                        </div>

                        <!-- 关键帧信息 -->
                        <div class="keyframe-info">
                            <p class="keyframe-desc">{{ (kf.visual_description || '').substring(0, 50) }}...</p>
                            <div class="keyframe-meta">
                                <span>{{ kf.duration }}秒</span>
                            </div>
                        </div>

                        <!-- 操作按钮 -->
                        <div class="keyframe-actions">
                            <el-button-group>
                                <el-button size="small" @click.stop="regenerateKeyframe(kf)">
                                    <el-icon><Refresh /></el-icon> 重新生成
                                </el-button>
                                <el-button
                                    v-if="kf.status === 'completed'"
                                    size="small"
                                    type="success"
                                    @click.stop="approveKeyframe(kf)">
                                    <el-icon><Check /></el-icon> 批准
                                </el-button>
                            </el-button-group>
                        </div>
                    </el-card>
                </div>
            </el-main>
        </el-container>

        <!-- 关键帧详情对话框 -->
        <keyframe-detail-dialog
            v-model="detailDialogVisible"
            :keyframe="selectedKeyframe"
            :project-id="project.project_id"
            @version-selected="onVersionSelected"
            @regenerate="regenerateKeyframe">
        </keyframe-detail-dialog>
    `,

    props: ['project'],

    data() {
        return {
            loading: false,
            generating: false,
            progress: 0,
            progressStatus: '',
            keyframes: [],
            selectedKeyframe: null,
            detailDialogVisible: false,
            ws: null,
            estimatedCost: 0,
            pollTimer: null
        }
    },

    computed: {
        hasKeyframes() {
            return this.keyframes.length > 0 && this.keyframes.some(kf => kf.status === 'completed');
        },
        approvedCount() {
            return this.keyframes.filter(kf => kf.status === 'approved').length;
        },
        allKeyframesApproved() {
            return this.keyframes.length > 0 && this.approvedCount === this.keyframes.length;
        }
    },

    async mounted() {
        await this.loadKeyframes();
        // M17: 只在有关键帧且部分正在生成时才轮询
        if (this.keyframes.length > 0 && this.keyframes.some(kf => kf.status === 'pending' || kf.status === 'generating')) {
            this.startPolling();
        }
    },

    methods: {
        async loadKeyframes() {
            this.loading = true;
            try {
                const response = await fetch(`/api/projects/${this.project.project_id}/keyframes`);
                if (!response.ok) {
                    throw new Error('加载关键帧失败');
                }
                const data = await response.json();
                this.keyframes = data.keyframes || [];
                this.estimatedCost = data.estimated_total_cost || 0;
                console.log('关键帧数据:', this.keyframes);
            } catch (error) {
                console.error('加载关键帧失败:', error);
                ElMessage.error('加载关键帧列表失败');
            } finally {
                this.loading = false;
            }
        },

        getSelectedImageUrl(kf) {
            // 先通过 selected_version_id 找
            if (kf.selected_version_id && kf.versions) {
                const v = kf.versions.find(v => v.version_id === kf.selected_version_id);
                if (v && v.image_url) return v.image_url;
            }
            // 找 is_selected 的
            if (kf.versions && kf.versions.length > 0) {
                const selected = kf.versions.find(v => v.is_selected);
                if (selected && selected.image_url) return selected.image_url;
                // 返回第一个有图的版本
                const first = kf.versions.find(v => v.image_url);
                if (first) return first.image_url;
            }
            return null;
        },

        getSelectedVersion(kf) {
            if (kf.selected_version_id && kf.versions) {
                return kf.versions.find(v => v.version_id === kf.selected_version_id) || null;
            }
            if (kf.versions && kf.versions.length > 0) {
                return kf.versions.find(v => v.is_selected) || kf.versions[0];
            }
            return null;
        },

        startPolling() {
            // H10: 先停止旧轮询，防止竞争
            this.stopPolling();
            // 每3秒轮询一次关键帧数据
            this.generating = true;
            this.pollTimer = setInterval(async () => {
                try {
                    const response = await fetch(`/api/projects/${this.project.project_id}/keyframes`);
                    if (response.ok) {
                        const data = await response.json();
                        this.keyframes = data.keyframes || [];

                        // 计算进度
                        const completed = this.keyframes.filter(kf => kf.status === 'completed' || kf.status === 'failed').length;
                        const total = this.keyframes.length || 1;
                        this.progress = completed / total;

                        if (data.generation_stage === 'keyframes' && this.keyframes.length > 0 &&
                            this.keyframes.every(kf => kf.status === 'completed' || kf.status === 'failed')) {
                            // 全部完成
                            this.generating = false;
                            this.progressStatus = 'success';
                            this.stopPolling();
                            ElMessage.success('关键帧生成完成！');
                        }
                    }
                } catch (e) {
                    console.error('轮询失败:', e);
                }
            }, 3000);
        },

        stopPolling() {
            if (this.pollTimer) {
                clearInterval(this.pollTimer);
                this.pollTimer = null;
            }
        },

        async generateKeyframes() {
            this.generating = true;
            this.progress = 0;

            try {
                const config = {
                    model: 'flux-pro',
                    quality: 'high',
                    aspect_ratio: '16:9',
                    optimize_prompt: true
                };

                const response = await fetch(`/api/projects/${this.project.project_id}/generate-keyframes`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                });

                if (!response.ok) {
                    throw new Error('创建生成任务失败');
                }

                const task = await response.json();
                console.log('关键帧生成任务:', task);

                ElMessage.success(`开始生成关键帧，预估成本: ¥${task.estimated_cost.toFixed(2)}`);

                // 使用WebSocket监听进度
                this.connectWebSocket(task.task_id);

            } catch (error) {
                console.error('生成关键帧失败:', error);
                ElMessage.error('生成关键帧失败: ' + error.message);
                this.generating = false;
            }
        },

        connectWebSocket(taskId) {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/keyframes/${taskId}`;

            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket已连接（关键帧生成）');
            };

            this.ws.onmessage = (event) => {
                let data;
                try { data = JSON.parse(event.data); } catch(_) { return; }
                console.log('进度更新:', data);

                this.progress = data.progress;

                if (data.status === 'completed') {
                    this.progressStatus = 'success';
                    ElMessage.success('关键帧生成完成！');
                    setTimeout(() => {
                        this.generating = false;
                        this.progress = 0;
                        this.loadKeyframes();
                    }, 2000);
                } else if (data.status === 'failed') {
                    this.progressStatus = 'exception';
                    ElMessage.error('关键帧生成失败：' + data.current_step);
                    this.generating = false;
                }
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket错误:', error);
                // H10: 先关闭WS再fallback到轮询
                if (this.ws) {
                    try { this.ws.close(); } catch(_) {}
                    this.ws = null;
                }
                this.startPolling();
            };

            this.ws.onclose = (event) => {
                console.log('WebSocket已关闭（关键帧生成）');
                // M20: 非正常关闭时重置状态+通知
                if (!event.wasClean && this.generating) {
                    this.generating = false;
                    ElMessage.warning('关键帧生成连接断开，请刷新查看状态');
                }
            };
        },

        cancelGeneration() {
            this.generating = false;
            this.stopPolling();
            if (this.ws) this.ws.close();
            ElMessage.info('已取消生成');
        },

        async approveAll() {
            for (const kf of this.keyframes) {
                if (kf.status === 'completed') {
                    try {
                        const versionId = kf.selected_version_id || 1;
                        const resp = await fetch(
                            `/api/shots/${this.project.project_id}/${kf.shot_id}/select-version`,
                            {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ version_id: versionId })
                            }
                        );
                        // H13: 只有API成功后才设状态
                        if (resp.ok) {
                            kf.status = 'approved';
                        } else {
                            console.error(`批准分镜${kf.shot_id}失败: HTTP ${resp.status}`);
                        }
                    } catch (e) {
                        console.error('批准失败:', e);
                    }
                }
            }
            ElMessage.success('已全部批准');
        },

        selectKeyframe(keyframe) {
            this.selectedKeyframe = keyframe;
            this.detailDialogVisible = true;
        },

        async regenerateKeyframe(keyframe) {
            // M19: 防重复点击
            if (keyframe._regenerating) return;
            keyframe._regenerating = true;
            try {
                // 标记为生成中
                keyframe.status = 'generating';
                ElMessage.info(`正在重新生成第 ${keyframe.shot_id} 个关键帧（3个版本）...`);

                const response = await fetch(
                    `/api/shots/${this.project.project_id}/${keyframe.shot_id}/regenerate-keyframe`,
                    {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            shot_id: keyframe.shot_id,
                            version_count: 3,
                            model: 'flux-pro',
                            optimize_prompt: true
                        })
                    }
                );

                if (!response.ok) {
                    throw new Error('服务器返回错误');
                }

                const versions = await response.json();
                console.log('新生成的版本:', versions);

                ElMessage.success(`已生成 ${versions.length} 个新版本，点击关键帧查看和选择`);
                await this.loadKeyframes();

            } catch (error) {
                console.error('重新生成失败:', error);
                keyframe.status = 'completed';
                ElMessage.error('重新生成失败，请稍后重试');
            } finally {
                keyframe._regenerating = false;
            }
        },

        async approveKeyframe(keyframe) {
            try {
                const versionId = keyframe.selected_version_id || 1;
                const response = await fetch(
                    `/api/shots/${this.project.project_id}/${keyframe.shot_id}/select-version`,
                    {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            version_id: versionId
                        })
                    }
                );

                if (!response.ok) {
                    throw new Error('批准失败');
                }

                keyframe.status = 'approved';
                ElMessage.success(`分镜 ${keyframe.shot_id} 已批准`);

            } catch (error) {
                console.error('批准失败:', error);
                ElMessage.error('批准失败: ' + error.message);
            }
        },

        onVersionSelected(data) {
            console.log('用户选择了版本:', data);
            this.loadKeyframes();
        },

        async startImageToVideo() {
            this.generating = true;
            this.progress = 0;
            this.progressStatus = '';

            try {
                ElMessage.info('开始图片生成视频...');

                const config = {
                    duration: 5,
                    model: 'kling-v1',
                    motion_strength: 0.5
                };

                const response = await fetch(`/api/projects/${this.project.project_id}/generate-videos`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(config)
                });

                if (!response.ok) {
                    throw new Error('创建视频生成任务失败');
                }

                const task = await response.json();
                console.log('视频生成任务:', task);

                ElMessage.success(`开始生成视频，预估成本: ¥${task.estimated_cost.toFixed(2)}`);
                this.connectVideoWebSocket(task.task_id);

            } catch (error) {
                console.error('生成视频失败:', error);
                ElMessage.error('生成视频失败: ' + error.message);
                this.generating = false;
            }
        },

        connectVideoWebSocket(taskId) {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/videos/${taskId}`;

            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket已连接（视频生成）');
            };

            this.ws.onmessage = (event) => {
                let data;
                try { data = JSON.parse(event.data); } catch(_) { return; }
                console.log('视频生成进度更新:', data);

                this.progress = data.progress;

                if (data.status === 'completed') {
                    this.progressStatus = 'success';
                    ElMessage.success('所有视频生成完成！');
                    setTimeout(() => {
                        this.generating = false;
                        this.progress = 0;
                        this.$emit('start-image-to-video');
                    }, 2000);
                } else if (data.status === 'failed') {
                    this.progressStatus = 'exception';
                    ElMessage.error('视频生成失败：' + data.current_step);
                    this.generating = false;
                }
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket错误:', error);
                ElMessage.error('连接失败，请检查服务器');
                this.generating = false;
            };

            this.ws.onclose = (event) => {
                console.log('WebSocket已关闭（视频生成）');
                if (!event.wasClean && this.generating) {
                    this.generating = false;
                    ElMessage.warning('视频生成连接断开，请刷新查看状态');
                }
            };
        },

        handleImageError(e) {
            e.target.style.display = 'none';
        }
    },

    beforeUnmount() {
        this.stopPolling();
        if (this.ws) {
            this.ws.close();
        }
    }
});

// ==================== 关键帧详情对话框组件 ====================

app.component('keyframe-detail-dialog', {
    template: `
        <el-dialog
            v-model="visible"
            title="关键帧详情与版本对比"
            width="90%"
            :close-on-click-modal="false">

            <div v-if="keyframe" class="keyframe-detail-content">
                <!-- 分镜信息 -->
                <el-descriptions :column="2" border>
                    <el-descriptions-item label="分镜ID">{{ keyframe.shot_id }}</el-descriptions-item>
                    <el-descriptions-item label="时长">{{ keyframe.duration }}秒</el-descriptions-item>
                    <el-descriptions-item label="视觉描述" :span="2">
                        {{ keyframe.visual_description }}
                    </el-descriptions-item>
                    <el-descriptions-item label="口播文案" :span="2">
                        {{ keyframe.narration }}
                    </el-descriptions-item>
                </el-descriptions>

                <!-- 版本对比 -->
                <h3 style="margin-top: 20px;">版本对比（点击选择）</h3>
                <el-row :gutter="20" class="version-comparison">
                    <el-col
                        :span="8"
                        v-for="version in keyframe.versions"
                        :key="version.version_id">
                        <el-card
                            class="version-card"
                            :class="{ 'selected': version.is_selected }"
                            shadow="hover"
                            @click="selectVersion(version)">

                            <template #header>
                                <div class="version-header">
                                    <span>版本 {{ version.version_id }}</span>
                                    <el-tag v-if="version.is_selected" type="success" size="small">
                                        <el-icon><Check /></el-icon> 已选择
                                    </el-tag>
                                </div>
                            </template>

                            <!-- 版本图片 -->
                            <div class="version-image">
                                <img :src="version.image_url" :alt="'Version ' + version.version_id" />
                            </div>

                            <!-- 生成信息 -->
                            <div class="version-meta">
                                <p><strong>模型:</strong> {{ version.model }}</p>
                                <p><strong>成本:</strong> ¥{{ version.cost.toFixed(2) }}</p>
                            </div>

                            <!-- 提示词 -->
                            <el-collapse>
                                <el-collapse-item title="查看提示词" name="prompt">
                                    <p style="font-size: 12px; color: #666;">{{ version.prompt }}</p>
                                </el-collapse-item>
                            </el-collapse>
                        </el-card>
                    </el-col>
                </el-row>

                <!-- 操作按钮 -->
                <div style="margin-top: 20px; text-align: center;">
                    <el-button @click="$emit('regenerate', keyframe)">
                        <el-icon><Refresh /></el-icon> 重新生成更多版本
                    </el-button>
                </div>
            </div>

            <template #footer>
                <el-button @click="visible = false">关闭</el-button>
            </template>
        </el-dialog>
    `,

    props: ['modelValue', 'keyframe', 'projectId'],

    computed: {
        visible: {
            get() { return this.modelValue },
            set(val) { this.$emit('update:modelValue', val) }
        }
    },

    methods: {
        async selectVersion(version) {
            try {
                const response = await fetch(
                    `/api/shots/${this.projectId}/${this.keyframe.shot_id}/select-version`,
                    {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ version_id: version.version_id })
                    }
                );

                if (!response.ok) {
                    throw new Error('选择版本失败');
                }

                ElMessage.success(`已选择版本 ${version.version_id}`);

                // 更新本地状态
                this.keyframe.versions.forEach(v => {
                    v.is_selected = (v.version_id === version.version_id);
                });
                this.keyframe.selected_version_id = version.version_id;

                this.$emit('version-selected', { shot_id: this.keyframe.shot_id, version_id: version.version_id });

            } catch (error) {
                console.error('选择版本失败:', error);
                ElMessage.error('选择版本失败: ' + error.message);
            }
        }
    }
});

// ==================== 分镜编辑器组件 ====================

app.component('shot-editor', {
    template: `
        <el-container class="editor-container">
            <!-- 左侧：分镜列表（可拖拽） -->
            <el-aside width="350px" class="shot-sidebar">
                <div class="sidebar-header">
                    <el-button @click="$emit('back')" :icon="ArrowLeft">返回</el-button>
                    <h3>分镜列表</h3>
                </div>

                <div v-if="loading" class="loading-shots">
                    <el-icon class="is-loading" :size="30"><Loading /></el-icon>
                    <p>加载中...</p>
                </div>

                <div v-else>
                    <div class="shots-info">
                        <el-tag>共 {{ shots.length }} 个分镜</el-tag>
                        <el-tag type="success">{{ totalDuration.toFixed(1) }}秒</el-tag>
                    </div>

                    <div id="shot-list" class="shot-list">
                        <div v-for="(shot, index) in shots"
                             :key="shot.shot_id"
                             :data-id="shot.shot_id"
                             class="shot-item"
                             :class="{ 'active': selectedShot && selectedShot.shot_id === shot.shot_id }"
                             @click="selectShot(shot)">
                            <div class="shot-number">{{ index + 1 }}</div>
                            <video :src="shot.video_url + '#t=0.1'" class="shot-thumb"></video>
                            <div class="shot-details">
                                <strong>{{ shot.filename }}</strong>
                                <span class="shot-duration">{{ shot.duration.toFixed(1) }}秒</span>
                            </div>
                            <el-icon class="drag-handle"><Rank /></el-icon>
                        </div>
                    </div>

                    <el-button type="primary" size="large" @click="$emit('export')" class="export-btn" block>
                        <el-icon><VideoCamera /></el-icon> 导出完整视频
                    </el-button>
                </div>
            </el-aside>

            <!-- 右侧：视频预览 -->
            <el-main class="video-preview">
                <div v-if="selectedShot" class="preview-content">
                    <h2>{{ selectedShot.filename }}</h2>
                    <video :src="selectedShot.video_url"
                           controls
                           class="video-player"
                           @loadedmetadata="onVideoLoaded">
                    </video>

                    <el-descriptions :column="1" border class="shot-metadata">
                        <el-descriptions-item label="分镜ID">{{ selectedShot.shot_id }}</el-descriptions-item>
                        <el-descriptions-item label="时长">{{ selectedShot.duration.toFixed(2) }}秒</el-descriptions-item>
                        <el-descriptions-item label="文件大小">{{ formatFileSize(selectedShot.file_size) }}</el-descriptions-item>
                        <el-descriptions-item label="视觉描述" v-if="selectedShot.visual_description">
                            {{ selectedShot.visual_description }}
                        </el-descriptions-item>
                        <el-descriptions-item label="口播文案" v-if="selectedShot.narration">
                            {{ selectedShot.narration }}
                        </el-descriptions-item>
                    </el-descriptions>
                </div>

                <el-empty v-else description="请从左侧选择一个分镜进行预览" :image-size="200"></el-empty>
            </el-main>
        </el-container>
    `,

    props: ['project'],

    data() {
        return {
            loading: false,
            shots: [],
            selectedShot: null,
            sortable: null
        }
    },

    computed: {
        totalDuration() {
            return this.shots.reduce((sum, shot) => sum + shot.duration, 0);
        }
    },

    async mounted() {
        await this.loadShots();
        this.initSortable();
    },

    beforeUnmount() {
        if (this.sortable) {
            this.sortable.destroy();
        }
    },

    methods: {
        async loadShots() {
            this.loading = true;
            try {
                const response = await fetch(`/api/projects/${this.project.project_id}/shots`);
                if (!response.ok) {
                    throw new Error('加载分镜列表失败');
                }
                const data = await response.json();
                this.shots = data.shots || [];
                console.log('分镜列表:', this.shots);

                if (this.shots.length > 0) {
                    this.selectedShot = this.shots[0];
                }
            } catch (error) {
                console.error('加载分镜失败:', error);
                ElMessage.error('加载分镜列表失败');
            } finally {
                this.loading = false;
            }
        },

        initSortable() {
            this.$nextTick(() => {
                const el = document.getElementById('shot-list');
                if (!el) return;

                this.sortable = Sortable.create(el, {
                    animation: 150,
                    handle: '.drag-handle',
                    ghostClass: 'sortable-ghost',
                    chosenClass: 'sortable-chosen',
                    dragClass: 'sortable-drag',
                    onEnd: this.onReorder
                });
            });
        },

        async onReorder(evt) {
            const newOrder = Array.from(evt.to.children).map(el =>
                parseInt(el.getAttribute('data-id'))
            );

            console.log('新顺序:', newOrder);

            try {
                const response = await fetch(`/api/projects/${this.project.project_id}/shots/reorder`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ shot_order: newOrder })
                });

                if (!response.ok) {
                    throw new Error('保存顺序失败');
                }

                ElMessage.success('分镜顺序已保存');

                const shotMap = {};
                this.shots.forEach(shot => {
                    shotMap[shot.shot_id] = shot;
                });
                this.shots = newOrder.map(id => shotMap[id]);

            } catch (error) {
                console.error('保存顺序失败:', error);
                ElMessage.error('保存分镜顺序失败');
                await this.loadShots();
            }
        },

        selectShot(shot) {
            this.selectedShot = shot;
        },

        onVideoLoaded(e) {
            console.log('视频已加载:', e.target.duration);
        },

        formatFileSize(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i];
        }
    }
});

// ==================== 导出对话框组件 ====================

app.component('export-dialog', {
    template: `
        <el-dialog
            v-model="visible"
            title="导出完整视频"
            width="600px"
            :close-on-click-modal="false">

            <el-form :model="config" label-width="120px">
                <el-form-item label="输出文件名">
                    <el-input v-model="config.output_filename"></el-input>
                </el-form-item>

                <el-form-item label="分辨率">
                    <el-select v-model="config.resolution" style="width: 100%">
                        <el-option label="1080P (1920x1080)" value="1920x1080"></el-option>
                        <el-option label="720P (1280x720)" value="1280x720"></el-option>
                        <el-option label="4K (3840x2160)" value="3840x2160"></el-option>
                    </el-select>
                </el-form-item>

                <el-form-item label="帧率">
                    <el-input-number v-model="config.fps" :min="24" :max="60" style="width: 100%"></el-input-number>
                </el-form-item>

                <el-form-item label="码率">
                    <el-input v-model="config.bitrate" placeholder="例如: 5M">
                        <template #append>bps</template>
                    </el-input>
                </el-form-item>
            </el-form>

            <!-- 进度条 -->
            <div v-if="exporting" class="export-progress">
                <el-progress :percentage="Math.round(progress * 100)" :status="progressStatus"></el-progress>
                <p class="progress-message">{{ progressMessage }}</p>
            </div>

            <template #footer>
                <el-button @click="visible = false" :disabled="exporting">取消</el-button>
                <el-button type="primary" @click="startExport" :loading="exporting">
                    {{ exporting ? '导出中...' : '开始导出' }}
                </el-button>
            </template>
        </el-dialog>
    `,

    props: ['modelValue', 'projectId'],

    data() {
        return {
            config: {
                output_filename: 'final_video.mp4',
                resolution: '1920x1080',
                fps: 30,
                bitrate: '5M'
            },
            exporting: false,
            progress: 0,
            progressMessage: '',
            progressStatus: '',
            ws: null
        }
    },

    computed: {
        visible: {
            get() { return this.modelValue },
            set(val) { this.$emit('update:modelValue', val) }
        }
    },

    methods: {
        async startExport() {
            if (!this.projectId) {
                ElMessage.error('项目ID未指定');
                return;
            }

            this.exporting = true;
            this.progress = 0;
            this.progressMessage = '准备导出...';
            this.progressStatus = '';

            try {
                const response = await fetch(`/api/projects/${this.projectId}/export`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.config)
                });

                if (!response.ok) {
                    throw new Error('创建导出任务失败');
                }

                const task = await response.json();
                console.log('导出任务:', task);
                this.connectWebSocket(task.task_id);

            } catch (error) {
                console.error('导出失败:', error);
                ElMessage.error('导出失败: ' + error.message);
                this.exporting = false;
            }
        },

        connectWebSocket(taskId) {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/export/${taskId}`;

            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket已连接');
            };

            this.ws.onmessage = (event) => {
                let data;
                try { data = JSON.parse(event.data); } catch(_) { return; }
                console.log('进度更新:', data);

                this.progress = data.progress;
                this.progressMessage = data.current_step;

                if (data.status === 'completed') {
                    this.progressStatus = 'success';
                    ElMessage.success('导出成功！');
                    setTimeout(() => {
                        this.visible = false;
                        this.exporting = false;
                        this.progress = 0;
                    }, 2000);
                } else if (data.status === 'failed') {
                    this.progressStatus = 'exception';
                    ElMessage.error('导出失败：' + data.current_step);
                    this.exporting = false;
                }
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket错误:', error);
                ElMessage.error('连接失败，请检查服务器');
                this.exporting = false;
            };

            this.ws.onclose = (event) => {
                console.log('WebSocket已关闭');
                if (!event.wasClean && this.exporting) {
                    this.exporting = false;
                    ElMessage.warning('导出连接断开，请重试');
                }
            };
        }
    },

    beforeUnmount() {
        if (this.ws) {
            this.ws.close();
        }
    }
});

// ==================== 个人IP工作室组件 ====================

app.component('ip-studio', {
    template: `
    <div style="max-width: 1100px; margin: 0 auto; padding: 20px;">
        <div class="list-header" style="margin-bottom: 24px;">
            <el-button @click="$emit('back')" :icon="ArrowLeft">返回项目列表</el-button>
            <h2 style="margin: 0;">🎙️ 个人IP工作室</h2>
            <div></div>
        </div>

        <!-- ===== IP 列表页 ===== -->
        <div v-if="subView === 'list'">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <div style="color: #606266; font-size: 14px;">为你的个人IP打造专属选题库和脚本，听起来像你自己写的</div>
                <el-button type="warning" size="large" @click="startNewInterview">
                    🎙️ 新建IP档案（AI访谈）
                </el-button>
            </div>

            <el-empty v-if="profiles.length === 0 && !loadingProfiles" description="还没有IP档案，点击右上角新建">
            </el-empty>

            <el-row :gutter="20" v-loading="loadingProfiles">
                <el-col :span="8" v-for="p in profiles" :key="p.profile_id" style="margin-bottom: 20px;">
                    <el-card shadow="hover" style="cursor: pointer;" @click="openWorkspace(p)">
                        <template #header>
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <span style="font-size: 18px; font-weight: bold;">{{ p.name }}</span>
                                    <el-tag size="small" type="warning" style="margin-left: 8px;">{{ p.industry }}</el-tag>
                                    <span v-if="p.role" style="font-size: 12px; color: #909399; margin-left: 6px;">{{ p.role }}</span>
                                </div>
                                <el-button text type="danger" size="small" @click.stop="deleteProfile(p)">删除</el-button>
                            </div>
                        </template>
                        <p style="font-size: 13px; color: #606266; margin: 0 0 12px; line-height: 1.6;">{{ p.ip_positioning }}</p>
                        <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px;">
                            <el-tag v-for="pillar in (p.content_pillars || []).slice(0,3)" :key="pillar" size="small" type="info">{{ pillar }}</el-tag>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: #909399;">
                            <span>已有 {{ p.topic_count || 0 }} 个选题</span>
                            <span>{{ formatDate(p.created_at) }}</span>
                        </div>
                    </el-card>
                </el-col>
            </el-row>
        </div>

        <!-- ===== AI 访谈页（3阶段） ===== -->
        <div v-else-if="subView === 'interview'" style="max-width: 720px; margin: 0 auto;">
            <el-card shadow="always">
                <template #header>
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <div style="width: 36px; height: 36px; border-radius: 50%; background: linear-gradient(135deg, #f59e0b, #ef4444); display: flex; align-items: center; justify-content: center; color: white; font-size: 14px; font-weight: bold; flex-shrink: 0;">记</div>
                        <div style="flex: 1;">
                            <div style="font-weight: bold; font-size: 15px;">{{ supplementProfileId ? 'AI记者 · 补充访谈' : 'AI记者 · 正在访谈' }}</div>
                            <div style="font-size: 12px; color: #909399;">{{ supplementProfileId ? '聊几个新话题，完善你的IP形象和观点库' : '约10-15分钟，请认真作答，答案越真实脚本越像你' }}</div>
                        </div>
                        <el-tag v-if="interviewDone" type="success">全部完成</el-tag>
                        <el-tag v-else type="warning">第 {{ chatHistory.filter(m=>m.role==='user').length }} 轮</el-tag>
                    </div>
                </template>

                <!-- 四阶段进度条 -->
                <div v-if="interviewStarted" style="display: flex; align-items: center; gap: 0; margin-bottom: 16px; padding: 12px 16px; background: #f8f9fa; border-radius: 8px;">
                    <div v-for="(phase, idx) in phaseList" :key="phase.key"
                        style="display: flex; align-items: center; flex: 1;">
                        <div style="display: flex; align-items: center; gap: 8px; flex: 1;">
                            <div :style="{
                                width: '28px', height: '28px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                                fontSize: '13px', fontWeight: 'bold', flexShrink: 0,
                                background: interviewPhase === phase.key ? '#f59e0b' : (phaseOrder(interviewPhase) > idx ? '#10b981' : '#e5e7eb'),
                                color: interviewPhase === phase.key || phaseOrder(interviewPhase) > idx ? 'white' : '#909399'
                            }">{{ phaseOrder(interviewPhase) > idx ? '✓' : (idx + 1) }}</div>
                            <div>
                                <div :style="{ fontSize: '13px', fontWeight: interviewPhase === phase.key ? 'bold' : 'normal', color: interviewPhase === phase.key ? '#f59e0b' : (phaseOrder(interviewPhase) > idx ? '#10b981' : '#909399') }">{{ phase.label }}</div>
                                <div style="font-size: 11px; color: #bbb;">{{ phase.desc }}</div>
                            </div>
                        </div>
                        <div v-if="idx < phaseList.length - 1" style="width: 30px; height: 2px; background: #e5e7eb; flex-shrink: 0;"></div>
                    </div>
                </div>

                <!-- 基本信息（访谈前填写） -->
                <div v-if="!interviewStarted" style="margin-bottom: 20px;">
                    <p style="color: #606266; margin-bottom: 16px; font-size: 14px;">{{ supplementProfileId ? '确认信息后开始补充访谈：' : '访谈开始前，先告诉我你的基本信息：' }}</p>
                    <el-form label-width="80px">
                        <el-form-item label="你的名字" required>
                            <el-input v-model="interviewee.name" placeholder="如：张总、李总、老王" size="large" :disabled="!!supplementProfileId"></el-input>
                        </el-form-item>
                        <el-form-item label="所在行业" required>
                            <el-input v-model="interviewee.industry" placeholder="如：餐饮、教育、制造业、电商" size="large" :disabled="!!supplementProfileId"></el-input>
                        </el-form-item>
                        <el-form-item label="你的角色">
                            <el-input v-model="interviewee.role" placeholder="如：创始人、总经理、合伙人" size="large" :disabled="!!supplementProfileId"></el-input>
                        </el-form-item>
                    </el-form>
                    <div style="display: flex; gap: 10px;">
                        <el-button v-if="supplementProfileId" @click="supplementProfileId = null; subView = 'workspace';">
                            ← 返回工作台
                        </el-button>
                        <el-button type="warning" size="large" @click="beginInterview"
                            :disabled="!interviewee.name.trim() || !interviewee.industry.trim()"
                            style="flex: 1; margin-top: 0; font-size: 15px;">
                            {{ supplementProfileId ? '🎙️ 开始补充访谈' : '🎙️ 开始接受访谈' }}
                        </el-button>
                    </div>
                </div>

                <!-- 聊天区域 -->
                <div v-if="interviewStarted">
                    <div ref="interviewChatBox" style="height: 420px; overflow-y: auto; padding: 16px; background: #f8f9fa; border-radius: 8px; margin-bottom: 14px;">
                        <div v-for="(msg, i) in chatHistory" :key="i" style="margin-bottom: 16px;">
                            <!-- 阶段切换提示 -->
                            <div v-if="msg.role === 'phase-transition'" style="text-align: center; padding: 12px; margin: 8px 0;">
                                <div style="display: inline-block; padding: 8px 20px; background: linear-gradient(135deg, #fef3c7, #fde68a); border-radius: 20px; font-size: 13px; color: #92400e; font-weight: bold;">
                                    {{ msg.content }}
                                </div>
                            </div>
                            <!-- AI记者 -->
                            <div v-else-if="msg.role === 'ai'" style="display: flex; align-items: flex-start; gap: 10px;">
                                <div style="width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, #f59e0b, #ef4444); display: flex; align-items: center; justify-content: center; color: white; font-size: 11px; font-weight: bold; flex-shrink: 0;">记</div>
                                <div style="background: white; border: 1px solid #fde68a; border-radius: 2px 12px 12px 12px; padding: 12px 16px; max-width: 85%; font-size: 14px; color: #303133; line-height: 1.7; box-shadow: 0 1px 4px rgba(0,0,0,0.06);">{{ msg.content }}</div>
                            </div>
                            <!-- 受访者 -->
                            <div v-else-if="msg.role === 'user'" style="display: flex; justify-content: flex-end; gap: 10px;">
                                <div style="background: #f59e0b; border-radius: 12px 2px 12px 12px; padding: 12px 16px; max-width: 85%; font-size: 14px; color: white; line-height: 1.7;">{{ msg.content }}</div>
                                <div style="width: 32px; height: 32px; border-radius: 50%; background: #6b7280; display: flex; align-items: center; justify-content: center; color: white; font-size: 11px; flex-shrink: 0;">我</div>
                            </div>
                        </div>
                        <div v-if="interviewLoading" style="display: flex; gap: 10px; align-items: center;">
                            <div style="width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, #f59e0b, #ef4444); display: flex; align-items: center; justify-content: center; color: white; font-size: 11px; flex-shrink: 0;">记</div>
                            <div style="background: white; border: 1px solid #fde68a; border-radius: 2px 12px 12px 12px; padding: 12px 16px; font-size: 14px; color: #909399;">
                                <el-icon class="is-loading"><Loading /></el-icon> 思考下一个问题...
                            </div>
                        </div>
                    </div>

                    <!-- 访谈进行中：输入框 -->
                    <div v-if="!interviewDone" style="display: flex; gap: 8px;">
                        <el-input v-model="currentAnswer" type="textarea" :rows="3"
                            placeholder="认真作答，答案越具体真实，最终脚本越像你自己写的...（说错了可以点「重答」）"
                            @keydown.ctrl.enter="submitAnswer"
                            :disabled="interviewLoading">
                        </el-input>
                        <div style="display: flex; flex-direction: column; gap: 4px; flex-shrink: 0;">
                            <el-button type="warning" @click="submitAnswer" :disabled="!currentAnswer.trim() || interviewLoading"
                                style="height: 50px; width: 80px; font-size: 13px;">
                                发送<br>(Ctrl+↵)
                            </el-button>
                            <el-button v-if="chatHistory.some(m => m.role === 'user') && !interviewLoading && !interviewDone"
                                type="info" plain size="small" @click="undoLastAnswer"
                                style="height: 26px; width: 80px; font-size: 11px;">
                                ↩ 重答
                            </el-button>
                        </div>
                    </div>

                    <!-- 访谈结束：提炼档案 -->
                    <div v-if="interviewDone" style="text-align: center; padding: 16px; background: #fef3c7; border-radius: 8px; border: 1px solid #fde68a;">
                        <div style="font-size: 16px; font-weight: bold; margin-bottom: 8px;">{{ supplementProfileId ? '🎉 补充访谈完成！' : '🎉 四阶段访谈全部完成！' }}</div>
                        <div style="color: #92400e; font-size: 13px; margin-bottom: 16px;">{{ supplementProfileId ? 'AI将提取新的观点和表达模式，追加到你的IP档案中...' : 'AI将基于你的背景、观点、思维方式和表达习惯，提炼专属IP档案（含观点素材库）...' }}</div>
                        <el-button type="warning" size="large" @click="finalizeProfile" :loading="finalizing" style="font-size: 15px; padding: 12px 40px;">
                            {{ finalizing ? (supplementProfileId ? '正在提取新观点...' : '正在提炼IP档案（含观点素材库+表达模式）...') : (supplementProfileId ? '更新我的IP档案 →' : '生成我的IP档案 →') }}
                        </el-button>
                    </div>
                </div>
            </el-card>
        </div>

        <!-- ===== 语音访谈页 ===== -->
        <div v-else-if="subView === 'voice-interview'" style="max-width: 720px; margin: 0 auto;">
            <el-card shadow="always" style="min-height: 600px; display: flex; flex-direction: column;">
                <template #header>
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <div style="width: 36px; height: 36px; border-radius: 50%; background: linear-gradient(135deg, #8b5cf6, #ec4899); display: flex; align-items: center; justify-content: center; color: white; font-size: 16px; flex-shrink: 0;">
                            <el-icon><Microphone /></el-icon>
                        </div>
                        <div style="flex: 1;">
                            <div style="font-weight: bold; font-size: 15px;">AI记者 · 语音访谈中</div>
                            <div style="font-size: 12px; color: #909399;">像打电话一样，直接说就行</div>
                        </div>
                        <el-tag v-if="voiceState === 'connecting'" type="info">连接中...</el-tag>
                        <el-tag v-else-if="voiceConnected" type="success">已连接</el-tag>
                    </div>
                </template>

                <!-- 四阶段进度条 -->
                <div style="display: flex; align-items: center; gap: 0; margin-bottom: 20px; padding: 12px 16px; background: #f8f9fa; border-radius: 8px;">
                    <div v-for="(phase, idx) in phaseList" :key="phase.key"
                        style="display: flex; align-items: center; flex: 1;">
                        <div style="display: flex; align-items: center; gap: 8px; flex: 1;">
                            <div :style="{
                                width: '28px', height: '28px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                                fontSize: '13px', fontWeight: 'bold', flexShrink: 0,
                                background: voicePhase === phase.key ? '#8b5cf6' : (phaseOrder(voicePhase) > idx ? '#10b981' : '#e5e7eb'),
                                color: voicePhase === phase.key || phaseOrder(voicePhase) > idx ? 'white' : '#909399'
                            }">{{ phaseOrder(voicePhase) > idx ? '✓' : (idx + 1) }}</div>
                            <div>
                                <div :style="{ fontSize: '13px', fontWeight: voicePhase === phase.key ? 'bold' : 'normal', color: voicePhase === phase.key ? '#8b5cf6' : (phaseOrder(voicePhase) > idx ? '#10b981' : '#909399') }">{{ phase.label }}</div>
                                <div style="font-size: 11px; color: #bbb;">{{ phase.desc }}</div>
                            </div>
                        </div>
                        <div v-if="idx < phaseList.length - 1" style="width: 30px; height: 2px; background: #e5e7eb; flex-shrink: 0;"></div>
                    </div>
                </div>

                <!-- 中央声波区域 -->
                <div style="flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 250px;">
                    <!-- 声波动画 -->
                    <div style="position: relative; width: 160px; height: 160px; margin-bottom: 24px;">
                        <div :style="{
                            width: '160px', height: '160px', borderRadius: '50%',
                            background: voiceState === 'ai_speaking' ? 'linear-gradient(135deg, #8b5cf6, #ec4899)' :
                                        voiceState === 'user_speaking' ? 'linear-gradient(135deg, #10b981, #06b6d4)' :
                                        'linear-gradient(135deg, #d1d5db, #9ca3af)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            transition: 'all 0.3s ease',
                            boxShadow: (voiceState === 'ai_speaking' || voiceState === 'user_speaking') ?
                                '0 0 40px rgba(139, 92, 246, 0.3)' : 'none'
                        }">
                            <div v-if="voiceState === 'ai_speaking'" style="color: white; font-size: 48px;">
                                <el-icon><ChatDotRound /></el-icon>
                            </div>
                            <div v-else-if="voiceState === 'user_speaking'" style="color: white; font-size: 48px;">
                                <el-icon><Microphone /></el-icon>
                            </div>
                            <div v-else-if="voiceState === 'thinking'" style="color: white; font-size: 48px;">
                                <el-icon class="is-loading"><Loading /></el-icon>
                            </div>
                            <div v-else-if="voiceState === 'connecting'" style="color: white; font-size: 48px;">
                                <el-icon class="is-loading"><Loading /></el-icon>
                            </div>
                            <div v-else style="color: white; font-size: 48px;">
                                <el-icon><Headset /></el-icon>
                            </div>
                        </div>
                        <!-- 脉冲动画 -->
                        <div v-if="voiceState === 'ai_speaking' || voiceState === 'user_speaking'" :style="{
                            position: 'absolute', top: '-10px', left: '-10px', width: '180px', height: '180px',
                            borderRadius: '50%', border: '2px solid',
                            borderColor: voiceState === 'ai_speaking' ? 'rgba(139,92,246,0.4)' : 'rgba(16,185,129,0.4)',
                            animation: 'voicePulse 1.5s ease-in-out infinite'
                        }"></div>
                    </div>

                    <!-- 状态文字 -->
                    <div style="font-size: 16px; font-weight: bold; color: #303133; margin-bottom: 8px;">
                        <span v-if="voiceState === 'connecting'">正在连接语音服务...</span>
                        <span v-else-if="voiceState === 'ai_speaking'" style="color: #8b5cf6;">AI正在说话...</span>
                        <span v-else-if="voiceState === 'user_speaking'" style="color: #10b981;">正在听你说...</span>
                        <span v-else-if="voiceState === 'thinking'" style="color: #f59e0b;">AI思考中...</span>
                        <span v-else-if="voiceConnected" style="color: #6b7280;">等待你说话...</span>
                        <span v-else>准备就绪</span>
                    </div>
                    <!-- 通话时长 + 轮数 -->
                    <div v-if="voiceConnected" style="display: flex; gap: 16px; font-size: 13px; color: #909399; margin-bottom: 8px;">
                        <span>{{ voiceDuration }}</span>
                        <span>第 {{ voiceTranscript.filter(t => t.role === 'user').length }} 轮</span>
                    </div>
                    <!-- 最新一句话（实时字幕） -->
                    <div v-if="voiceTranscript.length > 0" style="font-size: 13px; color: #606266; max-width: 400px; text-align: center; line-height: 1.5; min-height: 40px;">
                        {{ voiceTranscript.filter(t => t.role !== 'phase-transition').slice(-1)[0]?.text?.slice(0, 80) }}{{ (voiceTranscript.filter(t => t.role !== 'phase-transition').slice(-1)[0]?.text?.length || 0) > 80 ? '...' : '' }}
                    </div>
                </div>

                <!-- 实时转录折叠区 -->
                <el-collapse v-if="voiceTranscript.length > 0" style="margin-top: 16px;">
                    <el-collapse-item title="查看对话记录" name="transcript">
                        <div style="max-height: 200px; overflow-y: auto; padding: 8px;">
                            <div v-for="(t, i) in voiceTranscript" :key="i" style="margin-bottom: 10px;">
                                <div v-if="t.role === 'phase-transition'" style="text-align: center; padding: 8px;">
                                    <div style="display: inline-block; padding: 6px 16px; background: linear-gradient(135deg, #ede9fe, #ddd6fe); border-radius: 16px; font-size: 12px; color: #6d28d9; font-weight: bold;">
                                        {{ t.text }}
                                    </div>
                                </div>
                                <div v-else-if="t.role === 'ai'" style="display: flex; gap: 8px; align-items: flex-start;">
                                    <div style="width: 24px; height: 24px; border-radius: 50%; background: linear-gradient(135deg, #8b5cf6, #ec4899); display: flex; align-items: center; justify-content: center; color: white; font-size: 10px; flex-shrink: 0;">AI</div>
                                    <div style="font-size: 13px; color: #606266; line-height: 1.5;">{{ t.text }}</div>
                                </div>
                                <div v-else style="display: flex; gap: 8px; align-items: flex-start; justify-content: flex-end;">
                                    <div style="font-size: 13px; color: #303133; line-height: 1.5; text-align: right;">{{ t.text }}</div>
                                    <div style="width: 24px; height: 24px; border-radius: 50%; background: #6b7280; display: flex; align-items: center; justify-content: center; color: white; font-size: 10px; flex-shrink: 0;">我</div>
                                </div>
                            </div>
                        </div>
                    </el-collapse-item>
                </el-collapse>

                <!-- 底部按钮 -->
                <div style="display: flex; gap: 12px; justify-content: center; margin-top: 20px; padding-top: 16px; border-top: 1px solid #f0f0f0;">
                    <el-button :type="voiceMuted ? 'danger' : 'default'" circle size="large"
                        @click="toggleMute" :disabled="!voiceConnected">
                        <el-icon :size="20"><template v-if="voiceMuted"><CloseBold /></template><template v-else><Microphone /></template></el-icon>
                    </el-button>
                    <el-button type="danger" size="large" @click="stopVoiceInterview"
                        style="padding: 12px 32px; font-size: 15px;">
                        <el-icon style="margin-right: 6px;"><Phone /></el-icon>
                        结束通话
                    </el-button>
                </div>
            </el-card>
        </div>

        <!-- ===== IP 工作台 ===== -->
        <div v-else-if="subView === 'workspace' && currentProfile">
            <!-- 顶部：IP信息卡 -->
            <el-card style="margin-bottom: 20px; background: linear-gradient(135deg, #fffbeb, #fef3c7); border: 1px solid #fde68a;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 16px;">
                    <div style="flex: 1;">
                        <div style="font-size: 22px; font-weight: bold; margin-bottom: 4px;">{{ currentProfile.name }}</div>
                        <div style="color: #92400e; font-size: 14px; margin-bottom: 10px;">{{ currentProfile.industry }} · {{ currentProfile.role }}</div>
                        <div style="font-size: 14px; color: #78350f; line-height: 1.6; margin-bottom: 10px;">
                            <strong>IP定位：</strong>{{ currentProfile.ip_positioning }}
                        </div>
                        <div style="font-size: 13px; color: #92400e;">
                            <strong>说话风格：</strong>{{ currentProfile.speaking_style }}
                        </div>
                    </div>
                    <div style="min-width: 200px;">
                        <div style="margin-bottom: 8px; font-size: 12px; color: #92400e; font-weight: bold;">内容支柱</div>
                        <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px;">
                            <el-tag v-for="p in (currentProfile.content_pillars || [])" :key="p" type="warning" effect="light" size="small">{{ p }}</el-tag>
                        </div>
                        <div style="font-size: 12px; color: #92400e; font-weight: bold; margin-bottom: 6px;">目标受众</div>
                        <div style="font-size: 13px; color: #78350f;">{{ currentProfile.target_audience }}</div>
                    </div>
                </div>
            </el-card>

            <!-- 认知模型 + 声音指纹 折叠面板 -->
            <el-card v-if="hasEnhancedProfile" style="margin-bottom: 20px;">
                <template #header>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: bold; font-size: 15px;">🧠 认知模型 & 声音指纹</span>
                        <el-button text size="small" @click="showProfileDetails = !showProfileDetails">
                            {{ showProfileDetails ? '收起' : '展开详情' }}
                        </el-button>
                    </div>
                </template>

                <!-- 简要信息（始终显示） -->
                <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 8px;">
                    <el-tag v-for="tm in (currentProfile.thinking_models || []).slice(0, 4)" :key="tm" type="danger" effect="plain" size="small">{{ tm }}</el-tag>
                    <el-tag v-for="cv in (currentProfile.contrarian_views || []).slice(0, 2)" :key="cv" effect="plain" size="small">{{ cv }}</el-tag>
                </div>

                <!-- 详细面板 -->
                <div v-if="showProfileDetails" style="margin-top: 16px;">
                    <!-- 认知模型 -->
                    <div style="margin-bottom: 16px;">
                        <div style="font-size: 13px; font-weight: bold; color: #303133; margin-bottom: 8px;">思维模型</div>
                        <div style="display: flex; flex-wrap: wrap; gap: 6px;">
                            <el-tag v-for="tm in (currentProfile.thinking_models || [])" :key="tm" type="danger" effect="light">{{ tm }}</el-tag>
                        </div>
                    </div>
                    <div v-if="currentProfile.decision_framework" style="margin-bottom: 16px;">
                        <div style="font-size: 13px; font-weight: bold; color: #303133; margin-bottom: 4px;">决策方式</div>
                        <div style="font-size: 13px; color: #606266;">{{ currentProfile.decision_framework }}</div>
                    </div>

                    <!-- 情绪触发点 -->
                    <div v-if="currentProfile.emotional_triggers" style="margin-bottom: 16px;">
                        <div style="font-size: 13px; font-weight: bold; color: #303133; margin-bottom: 8px;">情绪触发点</div>
                        <div style="display: flex; gap: 16px; flex-wrap: wrap;">
                            <div v-if="(currentProfile.emotional_triggers.anger || []).length">
                                <div style="font-size: 12px; color: #ef4444; margin-bottom: 4px;">😡 愤怒</div>
                                <div v-for="a in currentProfile.emotional_triggers.anger" :key="a" style="font-size: 12px; color: #606266;">· {{ a }}</div>
                            </div>
                            <div v-if="(currentProfile.emotional_triggers.passion || []).length">
                                <div style="font-size: 12px; color: #f59e0b; margin-bottom: 4px;">🔥 热情</div>
                                <div v-for="p in currentProfile.emotional_triggers.passion" :key="p" style="font-size: 12px; color: #606266;">· {{ p }}</div>
                            </div>
                            <div v-if="(currentProfile.emotional_triggers.pride || []).length">
                                <div style="font-size: 12px; color: #10b981; margin-bottom: 4px;">💪 骄傲</div>
                                <div v-for="p in currentProfile.emotional_triggers.pride" :key="p" style="font-size: 12px; color: #606266;">· {{ p }}</div>
                            </div>
                        </div>
                    </div>

                    <!-- 逆主流观点 -->
                    <div v-if="(currentProfile.contrarian_views || []).length" style="margin-bottom: 16px;">
                        <div style="font-size: 13px; font-weight: bold; color: #303133; margin-bottom: 8px;">逆主流观点</div>
                        <div v-for="cv in currentProfile.contrarian_views" :key="cv" style="font-size: 13px; color: #78350f; padding: 6px 10px; background: #fffbeb; border-radius: 6px; margin-bottom: 4px; border-left: 3px solid #f59e0b;">
                            {{ cv }}
                        </div>
                    </div>

                    <!-- 声音指纹 -->
                    <div v-if="currentProfile.voice_fingerprint" style="margin-bottom: 16px; padding: 14px; background: #f0f9ff; border-radius: 8px; border: 1px solid #bae6fd;">
                        <div style="font-size: 13px; font-weight: bold; color: #0369a1; margin-bottom: 10px;">🎤 声音指纹</div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 12px;">
                            <div><span style="color: #0369a1; font-weight: bold;">句式：</span><span style="color: #475569;">{{ currentProfile.voice_fingerprint.sentence_pattern }}</span></div>
                            <div><span style="color: #0369a1; font-weight: bold;">修辞：</span><span style="color: #475569;">{{ currentProfile.voice_fingerprint.rhetoric_preference }}</span></div>
                            <div><span style="color: #0369a1; font-weight: bold;">论证：</span><span style="color: #475569;">{{ currentProfile.voice_fingerprint.argument_structure }}</span></div>
                            <div><span style="color: #0369a1; font-weight: bold;">比喻：</span><span style="color: #475569;">{{ currentProfile.voice_fingerprint.metaphor_domain }}</span></div>
                        </div>
                        <div v-if="(currentProfile.voice_fingerprint.forbidden_words || []).length" style="margin-top: 10px;">
                            <span style="font-size: 12px; color: #ef4444; font-weight: bold;">🚫 禁用词：</span>
                            <el-tag v-for="fw in currentProfile.voice_fingerprint.forbidden_words" :key="fw" size="small" type="danger" effect="plain" style="margin: 2px;">{{ fw }}</el-tag>
                        </div>
                        <div v-if="(currentProfile.voice_fingerprint.raw_quotes || []).length" style="margin-top: 10px;">
                            <div style="font-size: 12px; color: #0369a1; font-weight: bold; margin-bottom: 6px;">📝 原话摘录：</div>
                            <div v-for="q in currentProfile.voice_fingerprint.raw_quotes" :key="q" style="font-size: 12px; color: #475569; padding: 4px 8px; background: white; border-radius: 4px; margin-bottom: 3px; font-style: italic;">
                                "{{ q }}"
                            </div>
                        </div>
                    </div>

                    <!-- 观点素材库 -->
                    <div v-if="(currentProfile.opinion_bank || []).length" style="margin-bottom: 16px; padding: 14px; background: #fefce8; border-radius: 8px; border: 1px solid #fde047;">
                        <div style="font-size: 13px; font-weight: bold; color: #a16207; margin-bottom: 10px;">💡 观点素材库（{{ currentProfile.opinion_bank.length }}条）</div>
                        <div v-for="op in currentProfile.opinion_bank.slice(0, 5)" :key="op.opinion_id" style="font-size: 12px; padding: 8px; background: white; border-radius: 6px; margin-bottom: 6px; border-left: 3px solid #eab308;">
                            <div style="font-weight: bold; color: #78350f;">{{ op.topic }} · {{ op.stance }}</div>
                            <div style="color: #475569; font-style: italic; margin-top: 2px;">"{{ op.raw_expression }}"</div>
                        </div>
                    </div>

                    <!-- 表达模式 -->
                    <div v-if="currentProfile.expression_patterns && (currentProfile.expression_patterns.preferred_openings || []).length" style="margin-bottom: 16px; padding: 14px; background: #f0fdf4; border-radius: 8px; border: 1px solid #86efac;">
                        <div style="font-size: 13px; font-weight: bold; color: #15803d; margin-bottom: 10px;">🗣️ 表达模式</div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 12px;">
                            <div><span style="color: #15803d; font-weight: bold;">开场：</span><span style="color: #475569;">{{ (currentProfile.expression_patterns.preferred_openings || []).join('、') }}</span></div>
                            <div><span style="color: #15803d; font-weight: bold;">过渡：</span><span style="color: #475569;">{{ (currentProfile.expression_patterns.preferred_transitions || []).join('、') }}</span></div>
                            <div><span style="color: #15803d; font-weight: bold;">收尾：</span><span style="color: #475569;">{{ (currentProfile.expression_patterns.preferred_closings || []).join('、') }}</span></div>
                        </div>
                    </div>

                    <!-- 商业意图 -->
                    <div v-if="currentProfile.business_intent" style="margin-bottom: 16px;">
                        <div style="font-size: 13px; font-weight: bold; color: #303133; margin-bottom: 8px;">🎯 商业意图</div>
                        <div style="font-size: 12px; color: #606266; line-height: 1.8;">
                            <div><strong>核心目的：</strong>{{ currentProfile.business_intent.primary_goal }}</div>
                            <div><strong>目标印象：</strong>{{ currentProfile.business_intent.target_perception }}</div>
                            <div><strong>竞争差异：</strong>{{ currentProfile.business_intent.competitive_context }}</div>
                        </div>
                    </div>

                    <!-- 身份态度 -->
                    <div v-if="currentProfile.identity_attitude">
                        <div style="font-size: 13px; font-weight: bold; color: #303133; margin-bottom: 8px;">🎭 身份态度</div>
                        <div style="font-size: 12px; color: #606266; line-height: 1.8;">
                            <div><strong>身份定位：</strong>{{ currentProfile.identity_attitude.status_level }}</div>
                            <div><strong>沟通基调：</strong>{{ currentProfile.identity_attitude.communication_tone }}</div>
                            <div><strong>开场偏好：</strong>{{ currentProfile.identity_attitude.hook_preference }}</div>
                        </div>
                    </div>
                </div>
            </el-card>

            <!-- 快捷操作栏 -->
            <div style="display: flex; gap: 10px; margin-bottom: 20px;">
                <el-button type="warning" size="large" @click="autoFlow" :loading="generatingTopics || generatingScript"
                    style="font-size: 15px; padding: 12px 28px; font-weight: bold;">
                    🚀 一键生成脚本
                </el-button>
                <el-button type="info" plain @click="startSupplementInterview">
                    🎙️ 继续访谈（完善形象）
                </el-button>
            </div>

            <!-- 选题库 -->
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <h3 style="margin: 0;">📋 选题库 <span style="font-size: 13px; font-weight: normal; color: #909399;">（{{ topics.length }} 个选题）</span></h3>
                <el-button type="warning" @click="generateTopics" :loading="generatingTopics">
                    {{ topics.length > 0 ? '🔄 重新生成选题' : '✨ 生成选题库（15个）' }}
                </el-button>
            </div>

            <div v-if="generatingTopics" style="text-align: center; padding: 40px;">
                <el-icon class="is-loading" :size="40" style="color: #f59e0b;"><Loading /></el-icon>
                <p style="color: #909399; margin-top: 12px;">AI正在基于你的真实故事、观点和商业目标生成选题...</p>
            </div>

            <el-empty v-else-if="topics.length === 0" description="点击上方按钮，AI将基于你的IP档案生成15个专属选题">
            </el-empty>

            <!-- 选题卡片 -->
            <el-row :gutter="16" v-if="!generatingTopics">
                <el-col :span="12" v-for="topic in topics" :key="topic.topic_id" style="margin-bottom: 16px;">
                    <el-card shadow="hover" style="height: 100%;">
                        <template #header>
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px;">
                                <div style="flex: 1;">
                                    <el-tag :type="topicTypeTag(topic.type)" size="small" style="margin-bottom: 6px;">{{ topic.type }}</el-tag>
                                    <div style="font-weight: bold; font-size: 15px; line-height: 1.4;">{{ topic.title }}</div>
                                </div>
                                <el-button type="warning" size="small" @click="openScriptGenerator(topic)" style="flex-shrink: 0;">写脚本</el-button>
                            </div>
                        </template>
                        <div style="font-size: 13px; padding: 8px 12px; background: #fffbeb; border-radius: 6px; border-left: 3px solid #f59e0b; margin-bottom: 10px; color: #78350f; font-style: italic; line-height: 1.5;">
                            "{{ topic.hook_opening }}"
                        </div>
                        <div style="font-size: 12px; color: #606266; margin-bottom: 8px;">{{ topic.core_angle }}</div>
                        <div v-if="topic.strategic_angle" style="font-size: 11px; color: #0369a1; padding: 4px 8px; background: #f0f9ff; border-radius: 4px; margin-bottom: 6px;">
                            🎯 {{ topic.strategic_angle }}
                        </div>
                        <div v-if="topic.why_viral" style="font-size: 11px; color: #909399;">💡 {{ topic.why_viral }}</div>
                        <div style="margin-top: 8px; display: flex; justify-content: space-between; align-items: center;">
                            <div style="font-size: 11px; color: #bbb;">建议时长：{{ topic.estimated_duration }}秒</div>
                        </div>
                    </el-card>
                </el-col>
            </el-row>
        </div>

        <!-- ===== 脚本生成页（3步 + 段落反馈） ===== -->
        <div v-else-if="subView === 'script'" style="max-width: 900px; margin: 0 auto;">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
                <el-button text @click="subView = 'workspace'">← 返回选题库</el-button>
                <span style="color: #909399;">|</span>
                <span style="font-size: 14px; color: #606266;">当前选题：<strong>{{ currentTopic && currentTopic.title }}</strong></span>
            </div>

            <!-- 时长选择 + 生成按钮 -->
            <el-card style="margin-bottom: 20px;">
                <div style="display: flex; align-items: center; gap: 20px; flex-wrap: wrap;">
                    <span style="font-size: 14px; color: #303133; font-weight: bold;">脚本时长：</span>
                    <el-radio-group v-model="scriptDuration">
                        <el-radio-button :value="60">60秒</el-radio-button>
                        <el-radio-button :value="90">90秒</el-radio-button>
                        <el-radio-button :value="120">2分钟</el-radio-button>
                        <el-radio-button :value="180">3分钟</el-radio-button>
                    </el-radio-group>
                    <el-button type="warning" size="large" @click="generateScript" :loading="generatingScript" style="margin-left: auto;">
                        {{ generatingScript ? scriptStepText : (generatedScript ? '🔄 重新生成' : '✨ 生成脚本') }}
                    </el-button>
                </div>
                <div style="font-size: 12px; color: #909399; margin-top: 8px;">约 {{ Math.round(scriptDuration * 3.2) }} 字口播量 · 3步生成：思考→写稿→去AI味</div>
            </el-card>

            <!-- 生成中（分步进度） -->
            <div v-if="generatingScript" style="text-align: center; padding: 60px; background: #fffbeb; border-radius: 12px;">
                <el-icon class="is-loading" :size="50" style="color: #f59e0b;"><Loading /></el-icon>
                <h3 style="margin-top: 16px; color: #92400e;">{{ scriptStepText }}</h3>
                <div style="display: flex; justify-content: center; gap: 24px; margin-top: 16px;">
                    <div v-for="(step, i) in scriptSteps" :key="i" style="display: flex; align-items: center; gap: 6px;">
                        <div :style="{
                            width: '20px', height: '20px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                            fontSize: '11px', fontWeight: 'bold',
                            background: scriptStep > i ? '#10b981' : (scriptStep === i ? '#f59e0b' : '#e5e7eb'),
                            color: scriptStep >= i ? 'white' : '#909399'
                        }">{{ scriptStep > i ? '✓' : (i + 1) }}</div>
                        <span :style="{ fontSize: '12px', color: scriptStep === i ? '#92400e' : '#909399' }">{{ step }}</span>
                    </div>
                </div>
            </div>

            <!-- 思考备忘录（可展开） -->
            <el-card v-if="generatedScript && generatedScript.thinking_memo && !generatingScript" style="margin-bottom: 16px; border: 1px solid #e0e7ff;">
                <template #header>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 14px; color: #4338ca; font-weight: bold;">🧠 思考备忘录（AI以你的视角思考的过程）</span>
                        <el-button text size="small" @click="showThinkingMemo = !showThinkingMemo">
                            {{ showThinkingMemo ? '收起' : '展开' }}
                        </el-button>
                    </div>
                </template>
                <div v-if="showThinkingMemo" style="font-size: 13px; color: #475569; line-height: 1.8; white-space: pre-wrap;">{{ generatedScript.thinking_memo }}</div>
            </el-card>

            <!-- 脚本展示（段落卡片 + 反馈） -->
            <el-card v-if="generatedScript && !generatingScript">
                <template #header>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: bold; font-size: 16px;">📝 {{ generatedScript.topic_title }}</span>
                        <div style="display: flex; gap: 10px; align-items: center;">
                            <el-tag type="warning">{{ generatedScript.word_count }} 字</el-tag>
                            <el-tag>约 {{ generatedScript.duration }} 秒</el-tag>
                            <el-button size="small" @click="copyScript">复制全文</el-button>
                        </div>
                    </div>
                </template>

                <!-- 段落卡片（可编辑） -->
                <div v-for="(para, idx) in generatedScript.paragraphs" :key="para.paragraph_id || idx"
                    :style="{
                        padding: '14px 16px', marginBottom: '10px', borderRadius: '8px', position: 'relative',
                        background: rejectedParagraphs.includes(idx) ? '#fef2f2' : (paragraphEdits[idx] ? '#f0fdf4' : '#fafafa'),
                        border: rejectedParagraphs.includes(idx) ? '1px solid #fca5a5' : (paragraphEdits[idx] ? '1px solid #86efac' : '1px solid #e5e7eb'),
                        transition: 'all 0.2s'
                    }">
                    <!-- 编辑模式 -->
                    <div v-if="editingParagraph === idx">
                        <el-input v-model="editingText" type="textarea" :rows="4"
                            style="font-size: 15px; line-height: 1.9; margin-bottom: 8px;">
                        </el-input>
                        <div style="display: flex; gap: 8px; justify-content: flex-end;">
                            <el-button size="small" @click="cancelEdit">取消</el-button>
                            <el-button size="small" type="success" @click="saveEdit(idx)">保存编辑</el-button>
                        </div>
                    </div>
                    <!-- 展示模式 -->
                    <div v-else @dblclick="startEdit(idx)" style="cursor: text;">
                        <div style="font-size: 15px; line-height: 1.9; color: #303133;">{{ para.text || para }}</div>
                        <div v-if="paragraphEdits[idx]" style="margin-top: 6px;">
                            <el-tag size="small" type="success">已编辑</el-tag>
                        </div>
                    </div>
                    <div style="position: absolute; top: 8px; right: 8px; display: flex; gap: 4px;">
                        <el-button v-if="editingParagraph !== idx" text size="small" type="primary" @click="startEdit(idx)" style="font-size: 12px;">
                            ✏️ 编辑
                        </el-button>
                        <el-button v-if="!rejectedParagraphs.includes(idx) && editingParagraph !== idx" text size="small" type="danger" @click="rejectParagraph(idx)" style="font-size: 12px;">
                            👎 不像我
                        </el-button>
                        <el-button v-else-if="rejectedParagraphs.includes(idx) && editingParagraph !== idx" text size="small" type="success" @click="unrejectParagraph(idx)" style="font-size: 12px;">
                            ✅ 取消标记
                        </el-button>
                    </div>
                </div>

                <!-- 反馈提交区域 -->
                <div v-if="rejectedParagraphs.length > 0 || Object.keys(paragraphEdits).length > 0" style="margin-top: 16px; padding: 16px; background: #fef2f2; border-radius: 8px; border: 1px solid #fca5a5;">
                    <div style="font-size: 14px; font-weight: bold; color: #dc2626; margin-bottom: 8px;">
                        <span v-if="rejectedParagraphs.length > 0">已标记 {{ rejectedParagraphs.length }} 段"不像我"</span>
                        <span v-if="rejectedParagraphs.length > 0 && Object.keys(paragraphEdits).length > 0"> · </span>
                        <span v-if="Object.keys(paragraphEdits).length > 0" style="color: #16a34a;">已编辑 {{ Object.keys(paragraphEdits).length }} 段</span>
                    </div>
                    <el-input v-model="feedbackNotes" type="textarea" :rows="2"
                        placeholder="补充说明（可选）：哪里不对？比如'太正式了'、'我不会用这种词'..."
                        style="margin-bottom: 12px;">
                    </el-input>
                    <el-button type="danger" @click="submitFeedback" :loading="submittingFeedback" style="width: 100%;">
                        {{ submittingFeedback ? '正在分析并更新你的表达偏好...' : '提交反馈（更新我的表达偏好 + 记住编辑模式）' }}
                    </el-button>
                </div>
            </el-card>
        </div>

        <!-- H9: autoFlow选题对话框（移除dangerouslyUseHTMLString） -->
        <el-dialog v-model="autoFlowDialogVisible" title="选择一个选题，AI将自动生成脚本" width="600px">
            <div style="max-height: 400px; overflow-y: auto;">
                <div v-for="(topic, i) in topics" :key="topic.topic_id"
                    @click="autoFlowSelectedIndex = i"
                    :style="{
                        padding: '8px 12px', margin: '4px 0', borderRadius: '6px', cursor: 'pointer',
                        border: autoFlowSelectedIndex === i ? '2px solid #f59e0b' : '1px solid #fde68a',
                        background: autoFlowSelectedIndex === i ? '#fffbeb' : '#fff'
                    }">
                    <strong>{{ i + 1 }}. {{ topic.title }}</strong>
                    <div style="font-size: 12px; color: #92400e; margin-top: 4px;">{{ topic.hook_opening || '' }}</div>
                    <div style="font-size: 11px; color: #909399; margin-top: 2px;">{{ topic.type || '' }} · {{ topic.estimated_duration || 90 }}秒</div>
                </div>
            </div>
            <template #footer>
                <el-button @click="autoFlowDialogVisible = false">稍后再说</el-button>
                <el-button type="warning" @click="confirmAutoFlow">生成脚本</el-button>
            </template>
        </el-dialog>
    </div>
    `,

    data() {
        return {
            subView: 'list',   // 'list' | 'interview' | 'voice-interview' | 'workspace' | 'script'
            profiles: [],
            loadingProfiles: false,
            // 访谈（3阶段）
            interviewStarted: false,
            interviewee: { name: '', industry: '', role: '创始人' },
            chatHistory: [],
            currentAnswer: '',
            interviewLoading: false,
            interviewDone: false,
            interviewPhase: 'background', // 'background' | 'hot_topics' | 'cognitive' | 'voice'
            finalizing: false,
            // 语音访谈
            voiceWs: null,
            voiceConnected: false,
            voiceState: 'idle', // idle|connecting|ai_speaking|user_speaking|thinking
            voicePhase: 'background',
            voiceTranscript: [],  // [{role, text}]
            voiceMuted: false,
            voiceStartTime: null,
            voiceDuration: '00:00',
            _voiceTimer: null,
            audioContext: null,
            audioWorklet: null,
            mediaStream: null,
            aiAudioQueue: [],
            isPlayingAudio: false,
            voiceInterviewDoneData: null, // 存储访谈完成后的chat_history
            // 工作台
            currentProfile: null,
            showProfileDetails: false,
            topics: [],
            generatingTopics: false,
            // 脚本
            currentTopic: null,
            scriptDuration: 90,
            generatedScript: null,
            generatingScript: false,
            scriptStep: 0,       // 0=think, 1=write, 2=deai
            showThinkingMemo: false,
            // 反馈+编辑
            rejectedParagraphs: [],   // 被标记段落的index
            feedbackNotes: '',
            submittingFeedback: false,
            paragraphEdits: {},       // {paragraphIndex: {original, edited}} 编辑追踪
            editingParagraph: null,   // 当前正在编辑的段落index
            editingText: '',          // 编辑模式下的文本
            // 补充访谈
            supplementProfileId: null, // 非null时表示补充访谈模式
            // autoFlow选题dialog
            autoFlowDialogVisible: false,
            autoFlowSelectedIndex: 0,
            // M14: openWorkspace loading guard
            loadingWorkspace: false,
        }
    },

    computed: {
        phaseList() {
            return [
                { key: 'background', label: '背景采集', desc: '3-5轮' },
                { key: 'hot_topics', label: '热点观点', desc: '3-5轮' },
                { key: 'cognitive', label: '思维挖掘', desc: '4-6轮' },
                { key: 'voice', label: '表达采样', desc: '3-4轮' }
            ];
        },
        scriptSteps() {
            return ['以你的视角思考', '写稿', '去AI味'];
        },
        scriptStepText() {
            const texts = ['正在以你的视角思考...', '正在写稿...', '正在去AI味...'];
            return texts[this.scriptStep] || '生成中...';
        },
        hasEnhancedProfile() {
            if (!this.currentProfile) return false;
            return this.currentProfile.thinking_models || this.currentProfile.voice_fingerprint || this.currentProfile.business_intent || (this.currentProfile.opinion_bank && this.currentProfile.opinion_bank.length > 0);
        }
    },

    async mounted() {
        await this.loadProfiles();
    },

    methods: {
        phaseOrder(phase) {
            const order = { background: 0, hot_topics: 1, cognitive: 2, voice: 3, done: 4 };
            return order[phase] ?? 0;
        },

        async loadProfiles() {
            this.loadingProfiles = true;
            try {
                const resp = await fetch('/api/ip-studio/profiles');
                if (resp.ok) {
                    const data = await resp.json();
                    this.profiles = data.profiles || [];
                }
            } catch (e) {
                ElMessage.error('加载IP档案失败');
            } finally {
                this.loadingProfiles = false;
            }
        },

        async startNewInterview() {
            try {
                const { value } = await ElMessageBox.confirm(
                    '语音访谈：像打电话一样和AI对话，更自然高效（推荐）\n文字访谈：传统打字问答模式',
                    '选择访谈方式',
                    {
                        confirmButtonText: '语音访谈',
                        cancelButtonText: '文字访谈',
                        distinguishCancelAndClose: true,
                        type: 'info',
                    }
                );
                // 用户选择了语音访谈
                this.interviewStarted = false;
                this.interviewee = { name: '', industry: '', role: '创始人' };
                this.chatHistory = [];
                this.currentAnswer = '';
                this.interviewDone = false;
                this.interviewPhase = 'background';
                this.subView = 'interview';
                this._pendingVoice = true;
            } catch (action) {
                if (action === 'cancel') {
                    // 用户选择了文字访谈
                    this.interviewStarted = false;
                    this.interviewee = { name: '', industry: '', role: '创始人' };
                    this.chatHistory = [];
                    this.currentAnswer = '';
                    this.interviewDone = false;
                    this.interviewPhase = 'background';
                    this.subView = 'interview';
                    this._pendingVoice = false;
                }
                // action === 'close' 什么都不做
            }
        },

        async getNextQuestion(chatHistoryForApi) {
            const body = {
                name: this.interviewee.name,
                industry: this.interviewee.industry,
                chat_history: chatHistoryForApi || this.chatHistory,
                phase: this.interviewPhase
            };
            // hot_topics阶段传入热点话题
            if (this.interviewPhase === 'hot_topics' && this._hotTopicsText) {
                body.hot_topics = this._hotTopicsText;
            }
            const resp = await fetch('/api/ip-studio/interview/next-question', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            if (!resp.ok) throw new Error('获取问题失败');
            return await resp.json();
        },

        async beginInterview() {
            // 如果是语音模式，启动语音访谈
            if (this._pendingVoice) {
                this._pendingVoice = false;
                await this.startVoiceInterview();
                return;
            }
            this.interviewStarted = true;
            this.interviewLoading = true;
            try {
                const data = await this.getNextQuestion([]);
                this.chatHistory.push({ role: 'ai', content: data.question });
                this.$nextTick(() => this.scrollInterview());
            } catch (e) {
                this.chatHistory.push({ role: 'ai', content: `${this.interviewee.name}，你好！很高兴能采访你。先聊聊基本情况——你在${this.interviewee.industry}这个行业做了多久了？公司目前是什么规模？` });
            } finally {
                this.interviewLoading = false;
            }
        },

        async submitAnswer() {
            const answer = this.currentAnswer.trim();
            if (!answer || this.interviewLoading) return;

            this.chatHistory.push({ role: 'user', content: answer });
            this.currentAnswer = '';
            this.interviewLoading = true;
            this.$nextTick(() => this.scrollInterview());

            try {
                const data = await this.getNextQuestion();
                this.chatHistory.push({ role: 'ai', content: data.question });

                if (data.is_done) {
                    // 当前阶段结束，判断下一阶段
                    if (this.interviewPhase === 'background') {
                        this.interviewPhase = 'hot_topics';
                        this.chatHistory.push({ role: 'phase-transition', content: '✅ 背景采集完成 → 接下来聊几个行业热点话题' });
                        this.interviewLoading = true;
                        this.$nextTick(() => this.scrollInterview());
                        // 获取行业热点话题
                        try {
                            const htResp = await fetch(`/api/ip-studio/hot-topics/${encodeURIComponent(this.interviewee.industry)}`);
                            if (htResp.ok) {
                                const htData = await htResp.json();
                                this._hotTopicsText = (htData.topics || []).map(t => `- ${t.title}: ${t.angle || ''}`).join('\n');
                            }
                        } catch (e) {
                            console.warn('获取热点话题失败:', e);
                        }
                        try {
                            const nextData = await this.getNextQuestion();
                            this.chatHistory.push({ role: 'ai', content: nextData.question });
                        } catch (e) {
                            this.chatHistory.push({ role: 'ai', content: '最近AI对各行各业冲击挺大的，你觉得对你们行业影响大吗？' });
                        }
                    } else if (this.interviewPhase === 'hot_topics') {
                        this.interviewPhase = 'cognitive';
                        this.chatHistory.push({ role: 'phase-transition', content: '✅ 热点观点采集完成 → 接下来深入了解你的思维方式' });
                        this.interviewLoading = true;
                        this.$nextTick(() => this.scrollInterview());
                        try {
                            const nextData = await this.getNextQuestion();
                            this.chatHistory.push({ role: 'ai', content: nextData.question });
                        } catch (e) {
                            this.chatHistory.push({ role: 'ai', content: '你觉得你的行业里，大部分人在哪件事上是错的？' });
                        }
                    } else if (this.interviewPhase === 'cognitive') {
                        this.interviewPhase = 'voice';
                        this.chatHistory.push({ role: 'phase-transition', content: '✅ 思维挖掘完成 → 最后几个问题，感受你的表达方式' });
                        this.interviewLoading = true;
                        this.$nextTick(() => this.scrollInterview());
                        try {
                            const nextData = await this.getNextQuestion();
                            this.chatHistory.push({ role: 'ai', content: nextData.question });
                        } catch (e) {
                            this.chatHistory.push({ role: 'ai', content: '假装我是你的新员工，你怎么跟我解释你们公司是做什么的？就像平时跟人说一样' });
                        }
                    } else {
                        // voice阶段完成，访谈真正结束
                        this.interviewDone = true;
                    }
                }
            } catch (e) {
                this.chatHistory.push({ role: 'ai', content: '抱歉，我卡了一下。你刚才说的很有意思，能再具体说说吗？' });
            } finally {
                this.interviewLoading = false;
                this.$nextTick(() => this.scrollInterview());
            }
        },

        undoLastAnswer() {
            // 从后往前删掉最后一条ai + 最后一条user
            // 先找最后一条ai（可能是最后一条消息）
            let removedAi = false;
            let removedUser = false;
            for (let i = this.chatHistory.length - 1; i >= 0; i--) {
                if (!removedAi && this.chatHistory[i].role === 'ai') {
                    this.chatHistory.splice(i, 1);
                    removedAi = true;
                    continue;
                }
                if (removedAi && !removedUser && this.chatHistory[i].role === 'user') {
                    this.chatHistory.splice(i, 1);
                    removedUser = true;
                    break;
                }
            }
            if (removedUser) {
                ElMessage.info('已撤回上一条回答，请重新作答');
                this.$nextTick(() => this.scrollInterview());
            } else {
                ElMessage.info('没有可撤回的回答');
            }
        },

        async finalizeProfile() {
            // 如果是补充访谈模式
            if (this.supplementProfileId) {
                await this.finalizeSupplementInterview();
                return;
            }
            this.finalizing = true;
            try {
                // 过滤掉phase-transition消息，只发送ai和user消息
                const cleanHistory = this.chatHistory.filter(m => m.role === 'ai' || m.role === 'user');
                const resp = await fetch('/api/ip-studio/interview/finalize', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: this.interviewee.name,
                        industry: this.interviewee.industry,
                        role: this.interviewee.role,
                        chat_history: cleanHistory
                    })
                });
                if (!resp.ok) throw new Error('提炼失败');
                const data = await resp.json();
                ElMessage.success('IP档案已生成！即将自动生成选题...');
                this.currentProfile = data.profile;
                this.topics = [];
                this.subView = 'workspace';
                await this.loadProfiles();
                // 自动触发一条龙流程
                this.$nextTick(() => this.autoFlow());
            } catch (e) {
                ElMessage.error('IP档案提炼失败: ' + e.message);
            } finally {
                this.finalizing = false;
            }
        },

        async openWorkspace(profile) {
            // M14: 加载守卫 + 错误处理
            if (this.loadingWorkspace) return;
            this.loadingWorkspace = true;
            try {
                const resp = await fetch(`/api/ip-studio/profiles/${profile.profile_id}`);
                if (resp.ok) {
                    this.currentProfile = await resp.json();
                } else {
                    this.currentProfile = profile;
                }
                const tresp = await fetch(`/api/ip-studio/topics/${profile.profile_id}`);
                if (tresp.ok) {
                    const tdata = await tresp.json();
                    this.topics = tdata.topics || [];
                }
                this.showProfileDetails = false;
                this.subView = 'workspace';
            } catch (e) {
                console.error('打开工作台失败:', e);
                ElMessage.error('打开工作台失败，请重试');
            } finally {
                this.loadingWorkspace = false;
            }
        },

        async generateTopics() {
            if (!this.currentProfile) return;
            this.generatingTopics = true;
            try {
                const resp = await fetch('/api/ip-studio/topics/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ profile_id: this.currentProfile.profile_id, count: 15 })
                });
                if (!resp.ok) throw new Error('生成失败');
                const data = await resp.json();
                this.topics = data.topics || [];
                ElMessage.success(`已生成 ${this.topics.length} 个选题`);
            } catch (e) {
                ElMessage.error('选题生成失败: ' + e.message);
            } finally {
                this.generatingTopics = false;
            }
        },

        async autoFlow() {
            // 一条龙：自动生成选题 → 弹窗选题 → 自动生成脚本
            if (!this.currentProfile) return;

            // Step 1: 生成选题
            await this.generateTopics();
            if (!this.topics || this.topics.length === 0) return;

            // Step 2: 显示交互式选题dialog（H9: 移除dangerouslyUseHTMLString）
            this.autoFlowSelectedIndex = 0;
            this.autoFlowDialogVisible = true;
        },

        confirmAutoFlow() {
            // 用户从dialog中确认选题
            if (!this.topics || this.topics.length === 0) return;
            const selectedTopic = this.topics[this.autoFlowSelectedIndex] || this.topics[0];
            this.autoFlowDialogVisible = false;
            this.openScriptGenerator(selectedTopic);
            this.$nextTick(() => this.generateScript());
        },

        startSupplementInterview() {
            // 从workspace进入补充访谈模式
            if (!this.currentProfile || !this.currentProfile.name || !this.currentProfile.industry) {
                ElMessage.error('IP档案数据不完整，无法补充访谈');
                return;
            }
            this.supplementProfileId = this.currentProfile.profile_id;
            this.interviewee = {
                name: this.currentProfile.name,
                industry: this.currentProfile.industry,
                role: this.currentProfile.role || '创始人'
            };
            this.chatHistory = [];
            this.currentAnswer = '';
            this.interviewStarted = false;
            this.interviewDone = false;
            this.interviewPhase = 'hot_topics'; // 补充访谈跳过背景，直接从热点观点开始
            this.interviewLoading = false;
            this.subView = 'interview';
            ElMessage.info('补充访谈模式：聊几个新话题，完善你的IP形象');
        },

        async finalizeSupplementInterview() {
            // 补充访谈完成后调supplement接口
            if (!this.supplementProfileId) {
                ElMessage.error('补充访谈模式异常，请重新开始');
                return;
            }
            this.finalizing = true;
            try {
                const cleanHistory = this.chatHistory.filter(m => m.role === 'ai' || m.role === 'user');
                if (!cleanHistory.length) {
                    ElMessage.error('没有访谈记录，请先进行访谈');
                    this.finalizing = false;
                    return;
                }
                const resp = await fetch('/api/ip-studio/interview/supplement', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        profile_id: this.supplementProfileId,
                        chat_history: cleanHistory
                    })
                });
                if (!resp.ok) throw new Error('补充访谈提炼失败');
                const data = await resp.json();
                ElMessage.success('补充访谈已完成，观点素材库已更新！');
                this.currentProfile = data.profile;
                this.supplementProfileId = null;
                this.subView = 'workspace';
                await this.loadProfiles();
            } catch (e) {
                ElMessage.error('补充访谈失败: ' + e.message);
            } finally {
                this.finalizing = false;
            }
        },

        openScriptGenerator(topic) {
            this.currentTopic = topic;
            this.scriptDuration = parseInt(topic.estimated_duration) || 90;
            this.generatedScript = null;
            this.rejectedParagraphs = [];
            this.feedbackNotes = '';
            this.paragraphEdits = {};
            this.editingParagraph = null;
            this.scriptStep = 0;
            this.showThinkingMemo = false;
            this.subView = 'script';
        },

        async generateScript() {
            if (!this.currentProfile || !this.currentTopic) return;
            this.generatingScript = true;
            this.scriptStep = 0;
            this.rejectedParagraphs = [];
            this.feedbackNotes = '';
            this.paragraphEdits = {};
            this.editingParagraph = null;

            // 模拟3步进度
            this._scriptStepTimer = setInterval(() => {
                if (this.scriptStep < 2) this.scriptStep++;
            }, 8000);

            try {
                const resp = await fetch('/api/ip-studio/script/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        profile_id: this.currentProfile.profile_id,
                        topic: this.currentTopic,
                        duration: this.scriptDuration
                    })
                });
                if (!resp.ok) throw new Error('生成失败');
                const data = await resp.json();
                this.generatedScript = data.script;
                ElMessage.success('脚本生成成功！（已完成思考→写稿→去AI味三步）');
            } catch (e) {
                ElMessage.error('脚本生成失败: ' + e.message);
            } finally {
                clearInterval(this._scriptStepTimer);
                this.generatingScript = false;
            }
        },

        copyScript() {
            if (!this.generatedScript) return;
            navigator.clipboard.writeText(this.generatedScript.full_script).then(() => {
                ElMessage.success('脚本已复制到剪贴板');
            }).catch(() => {
                ElMessage.warning('请手动复制');
            });
        },

        // 段落反馈+编辑
        rejectParagraph(idx) {
            if (!this.rejectedParagraphs.includes(idx)) {
                this.rejectedParagraphs.push(idx);
            }
        },
        unrejectParagraph(idx) {
            this.rejectedParagraphs = this.rejectedParagraphs.filter(i => i !== idx);
        },
        startEdit(idx) {
            const para = this.generatedScript.paragraphs[idx];
            this.editingParagraph = idx;
            this.editingText = para.text || para;
        },
        cancelEdit() {
            this.editingParagraph = null;
            this.editingText = '';
        },
        saveEdit(idx) {
            const para = this.generatedScript.paragraphs[idx];
            const originalText = para.text || para;
            const editedText = this.editingText.trim();
            if (editedText && editedText !== originalText) {
                // M18: Vue响应式 — 创建新对象触发更新
                this.paragraphEdits = {...this.paragraphEdits, [idx]: {
                    original: originalText,
                    edited: editedText
                }};
                // 更新段落内容
                if (para.text !== undefined) {
                    para.text = editedText;
                } else {
                    this.generatedScript.paragraphs[idx] = editedText;
                }
                ElMessage.success('段落已保存，提交反馈时会记住你的修改模式');
            }
            this.editingParagraph = null;
            this.editingText = '';
        },
        async submitFeedback() {
            if (this.rejectedParagraphs.length === 0 && Object.keys(this.paragraphEdits).length === 0) return;
            this.submittingFeedback = true;
            try {
                // 收集rejected段落文本
                const rejectedTexts = this.rejectedParagraphs.map(idx => {
                    const para = this.generatedScript.paragraphs[idx];
                    return para.text || para;
                });

                // 收集编辑记录
                const edits = Object.entries(this.paragraphEdits).map(([idx, edit]) => ({
                    original_text: edit.original,
                    edited_text: edit.edited,
                    paragraph_index: parseInt(idx),
                    topic_title: this.generatedScript.topic_title || ''
                }));

                const resp = await fetch('/api/ip-studio/script/feedback', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        profile_id: this.currentProfile.profile_id,
                        rejected_paragraphs: rejectedTexts,
                        edits: edits,
                        notes: this.feedbackNotes
                    })
                });
                if (!resp.ok) throw new Error('提交失败');
                const data = await resp.json();

                let msg = '';
                if ((data.new_forbidden_words || []).length > 0) {
                    msg += `新增 ${data.new_forbidden_words.length} 个禁用词`;
                }
                if ((data.edits_processed || 0) > 0) {
                    msg += (msg ? '，' : '') + `分析了 ${data.edits_processed} 处编辑`;
                }
                if ((data.new_patterns || 0) > 0) {
                    msg += (msg ? '，' : '') + `学到 ${data.new_patterns} 个表达偏好`;
                }
                ElMessage.success(`已更新！${msg || '下次生成会自动调整'}`);

                // 重新加载档案
                const profileResp = await fetch(`/api/ip-studio/profiles/${this.currentProfile.profile_id}`);
                if (profileResp.ok) {
                    this.currentProfile = await profileResp.json();
                }

                this.rejectedParagraphs = [];
                this.feedbackNotes = '';
                this.paragraphEdits = {};
            } catch (e) {
                ElMessage.error('反馈提交失败: ' + e.message);
            } finally {
                this.submittingFeedback = false;
            }
        },

        async deleteProfile(profile) {
            try {
                await ElMessageBox.confirm(`确定删除「${profile.name}」的IP档案和所有选题吗？`, '确认删除', {
                    confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning'
                });
            } catch { return; }
            try {
                const resp = await fetch(`/api/ip-studio/profiles/${profile.profile_id}`, { method: 'DELETE' });
                if (!resp.ok) throw new Error('删除失败');
                ElMessage.success('已删除');
                await this.loadProfiles();
            } catch (e) {
                ElMessage.error('删除失败');
            }
        },

        // ===== 语音访谈方法 =====

        async startVoiceInterview() {
            const name = this.interviewee.name.trim();
            const industry = this.interviewee.industry.trim();
            const role = this.interviewee.role.trim() || '创始人';

            if (!name || !industry) {
                ElMessage.warning('请先填写姓名和行业');
                return;
            }

            // 请求麦克风权限
            try {
                this.mediaStream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        sampleRate: 24000,
                        channelCount: 1,
                        echoCancellation: true,
                        noiseSuppression: true,
                    }
                });
            } catch (e) {
                ElMessage.error('无法访问麦克风，请检查权限设置。将切换到文字模式。');
                this._pendingVoice = false;
                this.interviewStarted = true;
                this.interviewLoading = true;
                try {
                    const data = await this.getNextQuestion([]);
                    this.chatHistory.push({ role: 'ai', content: data.question });
                } catch (e2) {
                    this.chatHistory.push({ role: 'ai', content: `${name}，你好！先聊聊基本情况——你在${industry}做了多久了？` });
                } finally {
                    this.interviewLoading = false;
                }
                return;
            }

            // 切换到语音视图
            this.voiceState = 'connecting';
            this.voiceConnected = false;
            this.voicePhase = 'background';
            this.voiceTranscript = [];
            this.voiceMuted = false;
            this.voiceInterviewDoneData = null;
            this.subView = 'voice-interview';

            // 建立WebSocket（H4配合: 加token参数）
            const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsToken = sessionStorage.getItem('ws_token') || document.cookie.replace(/(?:(?:^|.*;\s*)session_token\s*=\s*([^;]*).*$)|^.*$/, '$1') || 'anonymous_' + Date.now();
            if (!sessionStorage.getItem('ws_token')) {
                // 首次使用时生成并保存一个随机 token
                const generatedToken = 'ws_' + Math.random().toString(36).substring(2, 15) + Date.now().toString(36);
                sessionStorage.setItem('ws_token', generatedToken);
            }
            const wsUrl = `${protocol}//${location.host}/api/ip-studio/interview/live?token=${encodeURIComponent(sessionStorage.getItem('ws_token'))}`;

            try {
                this.voiceWs = new WebSocket(wsUrl);
                this.voiceWs.onopen = () => {
                    // 发送init消息
                    this.voiceWs.send(JSON.stringify({
                        type: 'init',
                        name: name,
                        industry: industry,
                        role: role
                    }));
                };
                this.voiceWs.onmessage = (event) => this.handleVoiceWsMessage(event);
                this.voiceWs.onclose = (event) => {
                    if (this.voiceConnected && this.subView === 'voice-interview') {
                        this.voiceConnected = false;
                        this.voiceState = 'idle';
                        if (!this.voiceInterviewDoneData) {
                            if (!event.wasClean) {
                                ElMessage.error('语音连接异常断开，请刷新页面重试');
                            } else {
                                ElMessage.warning('语音连接已断开');
                            }
                        }
                    }
                };
                this.voiceWs.onerror = (e) => {
                    console.error('Voice WS error:', e);
                    ElMessage.error('语音连接出错');
                    this.voiceState = 'idle';
                };
            } catch (e) {
                ElMessage.error('无法建立语音连接');
                this.cleanupVoice();
                this.subView = 'list';
            }
        },

        handleVoiceWsMessage(event) {
            let msg;
            try {
                msg = JSON.parse(event.data);
            } catch (e) {
                return;
            }

            switch (msg.type) {
                case 'connected':
                    this.voiceConnected = true;
                    this.voiceState = 'idle';
                    // 启动音频采集
                    this.startAudioCapture();
                    // 启动通话计时
                    this.voiceStartTime = Date.now();
                    this._voiceTimer = setInterval(() => {
                        const sec = Math.floor((Date.now() - this.voiceStartTime) / 1000);
                        const m = String(Math.floor(sec / 60)).padStart(2, '0');
                        const s = String(sec % 60).padStart(2, '0');
                        this.voiceDuration = `${m}:${s}`;
                    }, 1000);
                    ElMessage.success('语音连接成功，开始访谈');
                    break;

                case 'ai_audio':
                    this.playAiAudio(msg.data);
                    break;

                case 'ai_speaking_start':
                    this.voiceState = 'ai_speaking';
                    break;

                case 'ai_speaking_done':
                    // 只有当前在ai_speaking状态才切回idle，避免覆盖thinking等状态
                    if (this.voiceState === 'ai_speaking') {
                        this.voiceState = 'idle';
                    }
                    break;

                case 'user_speaking_start':
                    this.voiceState = 'user_speaking';
                    // 用户开口打断AI → 销毁旧播放ctx，彻底停止所有排队的音频
                    if (this._playbackCtx) {
                        try { this._playbackCtx.close(); } catch(e) {}
                        this._playbackCtx = null;
                    }
                    this._nextPlayTime = 0;
                    break;

                case 'user_speaking_done':
                    this.voiceState = 'thinking';
                    break;

                case 'transcript':
                    if (msg.text && msg.text.trim()) {
                        this.voiceTranscript.push({
                            role: msg.role,
                            text: msg.text
                        });
                    }
                    break;

                case 'phase_change':
                    this.voicePhase = msg.phase;
                    this.voiceTranscript.push({
                        role: 'phase-transition',
                        text: msg.message || `进入${msg.phase}阶段`
                    });
                    ElMessage.info(`阶段切换：${msg.message || msg.phase}`);
                    break;

                case 'interview_done':
                    this.voiceInterviewDoneData = msg.chat_history;
                    ElMessage.success('访谈完成！');
                    this.finishVoiceInterview(msg.chat_history);
                    break;

                case 'error':
                    ElMessage.error(msg.message || '语音访谈出错');
                    console.error('Voice interview error:', msg.message);
                    break;
            }
        },

        async startAudioCapture() {
            if (!this.mediaStream) return;

            try {
                // 采集用独立的 AudioContext，不连扬声器
                this._captureCtx = new AudioContext({ sampleRate: 24000 });

                // 加载 AudioWorklet
                await this._captureCtx.audioWorklet.addModule('/static/js/audio-processor.js');

                const source = this._captureCtx.createMediaStreamSource(this.mediaStream);
                this.audioWorklet = new AudioWorkletNode(this._captureCtx, 'audio-capture');

                this.audioWorklet.port.onmessage = (e) => {
                    // AI说话时不发送麦克风音频，防止AI声音被拾取导致自问自答
                    if (this.voiceMuted || this.voiceState === 'ai_speaking' || !this.voiceWs || this.voiceWs.readyState !== WebSocket.OPEN) return;

                    // ArrayBuffer → base64
                    const pcm16 = new Uint8Array(e.data);
                    let binary = '';
                    for (let i = 0; i < pcm16.length; i++) {
                        binary += String.fromCharCode(pcm16[i]);
                    }
                    const base64 = btoa(binary);
                    this.voiceWs.send(JSON.stringify({ type: 'audio', data: base64 }));
                };

                source.connect(this.audioWorklet);
                // 必须连到 destination 才能让 process() 被调用，但用静音 GainNode 避免回声
                const silentGain = this._captureCtx.createGain();
                silentGain.gain.value = 0;
                this.audioWorklet.connect(silentGain);
                silentGain.connect(this._captureCtx.destination);
                console.log('Audio capture started');
            } catch (e) {
                console.error('Audio capture setup failed:', e);
                ElMessage.error('音频采集初始化失败');
            }
        },

        playAiAudio(base64Chunk) {
            // 播放用独立的 AudioContext
            if (!this._playbackCtx) {
                this._playbackCtx = new AudioContext({ sampleRate: 24000 });
                this._nextPlayTime = 0;
            }

            try {
                // base64 → PCM16 → Float32
                const binary = atob(base64Chunk);
                const bytes = new Uint8Array(binary.length);
                for (let i = 0; i < binary.length; i++) {
                    bytes[i] = binary.charCodeAt(i);
                }
                const pcm16 = new Int16Array(bytes.buffer);
                const float32 = new Float32Array(pcm16.length);
                for (let i = 0; i < pcm16.length; i++) {
                    float32[i] = pcm16[i] / 32768.0;
                }

                // 创建AudioBuffer
                const audioBuffer = this._playbackCtx.createBuffer(1, float32.length, 24000);
                audioBuffer.getChannelData(0).set(float32);

                // 排队播放：每个chunk接在上一个后面，不叠加
                const now = this._playbackCtx.currentTime;
                const startTime = Math.max(now, this._nextPlayTime || 0);
                this._nextPlayTime = startTime + audioBuffer.duration;

                const bufferSource = this._playbackCtx.createBufferSource();
                bufferSource.buffer = audioBuffer;
                bufferSource.connect(this._playbackCtx.destination);
                bufferSource.start(startTime);
            } catch (e) {
                console.error('Audio playback error:', e);
            }
        },

        toggleMute() {
            this.voiceMuted = !this.voiceMuted;
            if (this.mediaStream) {
                this.mediaStream.getAudioTracks().forEach(track => {
                    track.enabled = !this.voiceMuted;
                });
            }
            ElMessage.info(this.voiceMuted ? '麦克风已静音' : '麦克风已开启');
        },

        async stopVoiceInterview() {
            try {
                await ElMessageBox.confirm(
                    '确定结束通话吗？访谈记录将被保存。',
                    '结束通话',
                    { confirmButtonText: '结束', cancelButtonText: '继续', type: 'warning' }
                );
            } catch {
                return;
            }

            // 发送结束信号
            if (this.voiceWs && this.voiceWs.readyState === WebSocket.OPEN) {
                this.voiceWs.send(JSON.stringify({ type: 'end_call' }));
                // 等待服务器返回 interview_done
                // 如果3秒内没收到，强制使用已有transcript
                setTimeout(() => {
                    if (!this.voiceInterviewDoneData) {
                        const chatHistory = this.voiceTranscript
                            .filter(t => t.role === 'user' || t.role === 'ai')
                            .map(t => ({ role: t.role, content: t.text }));
                        this.finishVoiceInterview(chatHistory);
                    }
                }, 3000);
            } else {
                // WebSocket已断开，使用已有transcript
                const chatHistory = this.voiceTranscript
                    .filter(t => t.role === 'user' || t.role === 'ai')
                    .map(t => ({ role: t.role, content: t.text }));
                this.finishVoiceInterview(chatHistory);
            }
        },

        async finishVoiceInterview(chatHistory) {
            // 清理音频资源
            this.cleanupVoice();

            if (!chatHistory || chatHistory.length < 2) {
                ElMessage.warning('对话记录为空，无法生成档案。');
                this.subView = 'list';
                return;
            }

            // 转到文字访谈的finalize流程
            this.interviewee = {
                name: this.interviewee.name,
                industry: this.interviewee.industry,
                role: this.interviewee.role || '创始人'
            };
            this.chatHistory = chatHistory;
            this.interviewDone = true;
            this.interviewStarted = true;
            this.subView = 'interview';

            // 自动触发finalize
            await this.finalizeProfile();
        },

        cleanupVoice() {
            // 停止计时
            if (this._voiceTimer) {
                clearInterval(this._voiceTimer);
                this._voiceTimer = null;
            }
            // 关闭WebSocket
            if (this.voiceWs) {
                try { this.voiceWs.close(); } catch(e) {}
                this.voiceWs = null;
            }
            // 关闭采集AudioContext
            if (this._captureCtx) {
                try { this._captureCtx.close(); } catch(e) {}
                this._captureCtx = null;
            }
            // 关闭播放AudioContext
            if (this._playbackCtx) {
                try { this._playbackCtx.close(); } catch(e) {}
                this._playbackCtx = null;
            }
            this._nextPlayTime = 0;
            // 关闭麦克风
            if (this.mediaStream) {
                this.mediaStream.getTracks().forEach(t => t.stop());
                this.mediaStream = null;
            }
            this.audioWorklet = null;
            this.voiceConnected = false;
            this.voiceState = 'idle';
        },

        scrollInterview() {
            if (this.$refs.interviewChatBox) {
                this.$refs.interviewChatBox.scrollTop = this.$refs.interviewChatBox.scrollHeight;
            }
        },

        topicTypeTag(type) {
            const map = { '故事型': 'warning', '观点型': 'danger', '干货型': 'success', '日常型': 'info', '争议型': '' };
            return map[type] || 'info';
        },

        formatDate(dt) {
            if (!dt) return '';
            return new Date(dt).toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' });
        }
    },

    // H12: beforeUnmount 清理语音资源和定时器
    beforeUnmount() {
        this.cleanupVoice();
        if (this._scriptStepTimer) clearInterval(this._scriptStepTimer);
    }
});

// ==================== 模板库组件 ====================

app.component('template-library', {
    template: `
        <div style="max-width: 1200px; margin: 0 auto; padding: 20px;">
            <div class="list-header" style="margin-bottom: 24px;">
                <el-button @click="$emit('back')" :icon="ArrowLeft">返回项目列表</el-button>
                <h2 style="margin: 0;">📋 内容模板库</h2>
                <div></div>
            </div>

            <el-tabs v-model="activeTab" @tab-click="onTabChange">
                <!-- ===== 系统模板 ===== -->
                <el-tab-pane label="系统模板" name="system">
                    <div style="margin-bottom: 16px; display: flex; gap: 10px; flex-wrap: wrap; align-items: center;">
                        <span style="font-size: 13px; color: #606266;">来源筛选：</span>
                        <el-tag v-for="f in sourceFilters" :key="f.value"
                            @click="sourceFilter = (sourceFilter === f.value ? null : f.value)"
                            :effect="sourceFilter === f.value ? 'dark' : 'plain'"
                            style="cursor: pointer;">{{ f.label }}</el-tag>
                    </div>
                    <el-row :gutter="16" v-loading="loadingSystem">
                        <el-col :span="8" v-for="tpl in filteredSystemTemplates" :key="tpl.template_id" style="margin-bottom: 16px;">
                            <el-card shadow="hover" style="height: 100%;">
                                <template #header>
                                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                        <div>
                                            <div style="font-weight: bold; font-size: 15px; margin-bottom: 4px;">{{ tpl.name }}</div>
                                            <el-tag size="small" :type="sourceTagType(tpl.source.type)">{{ tpl.source.label }}</el-tag>
                                        </div>
                                        <el-button size="small" type="primary" plain @click="openCloneDialog(tpl)">克隆定制</el-button>
                                    </div>
                                </template>
                                <div style="font-size: 12px; color: #909399; margin-bottom: 8px; line-height: 1.5;">{{ tpl.source.bio }}</div>
                                <div style="font-size: 13px; color: #303133; margin-bottom: 10px;">{{ tpl.core_strategy }}</div>
                                <div style="font-size: 12px; color: #606266; background: #f5f7fa; padding: 8px; border-radius: 6px;">
                                    <strong>开场公式：</strong>{{ tpl.hook_formula }}
                                </div>
                                <div style="margin-top: 8px; display: flex; flex-wrap: wrap; gap: 4px;">
                                    <el-tag v-for="cat in (tpl.suitable_categories || []).slice(0,3)" :key="cat" size="small" type="info">{{ cat }}</el-tag>
                                    <el-tag size="small">{{ tpl.best_duration }}</el-tag>
                                </div>
                            </el-card>
                        </el-col>
                    </el-row>
                </el-tab-pane>

                <!-- ===== 我的模板 ===== -->
                <el-tab-pane name="user">
                    <template #label>
                        我的模板
                        <el-badge v-if="userTemplates.length > 0" :value="userTemplates.length" type="primary" style="margin-left: 4px;"></el-badge>
                    </template>

                    <div style="margin-bottom: 20px; display: flex; gap: 12px;">
                        <el-button type="primary" @click="extractDialogVisible = true">
                            📄 从脚本提炼
                        </el-button>
                        <el-button plain @click="cloneDialogVisible = true; cloneTarget = null">
                            📋 克隆系统模板
                        </el-button>
                    </div>

                    <el-empty v-if="userTemplates.length === 0 && !loadingUser"
                        description="还没有自建模板，快去创建第一个吧！">
                    </el-empty>

                    <el-row :gutter="16" v-loading="loadingUser">
                        <el-col :span="8" v-for="tpl in userTemplates" :key="tpl.template_id" style="margin-bottom: 16px;">
                            <el-card shadow="hover" style="height: 100%; border: 1px solid #d4edda;">
                                <template #header>
                                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                                        <div>
                                            <div style="font-weight: bold; font-size: 15px; margin-bottom: 4px;">{{ tpl.name }}</div>
                                            <el-tag size="small" type="success">{{ tpl.source.label }}</el-tag>
                                            <el-tag v-if="tpl.cloned_from" size="small" type="info" style="margin-left: 4px;">克隆自系统</el-tag>
                                        </div>
                                        <div style="display: flex; gap: 6px;">
                                            <el-button size="small" @click="openEditDialog(tpl)" text type="primary">编辑</el-button>
                                            <el-button size="small" @click="deleteUserTemplate(tpl)" text type="danger">删除</el-button>
                                        </div>
                                    </div>
                                </template>
                                <div style="font-size: 13px; color: #303133; margin-bottom: 10px;">{{ tpl.core_strategy }}</div>
                                <div style="font-size: 12px; color: #606266; background: #f0f9f0; padding: 8px; border-radius: 6px;">
                                    <strong>开场公式：</strong>{{ tpl.hook_formula }}
                                </div>
                                <div style="margin-top: 8px; display: flex; flex-wrap: wrap; gap: 4px;">
                                    <el-tag v-for="cat in (tpl.suitable_categories || []).slice(0,3)" :key="cat" size="small" type="info">{{ cat }}</el-tag>
                                    <el-tag size="small">{{ tpl.best_duration }}</el-tag>
                                </div>
                            </el-card>
                        </el-col>
                    </el-row>
                </el-tab-pane>
            </el-tabs>

            <!-- ===== 从脚本提炼对话框 ===== -->
            <el-dialog v-model="extractDialogVisible" title="📄 从脚本提炼模板" width="680px" :close-on-click-modal="false">
                <div v-if="!extractPreview">
                    <el-form label-width="80px">
                        <el-form-item label="模板名称" required>
                            <el-input v-model="extractForm.name" placeholder="给这个方法论起个名字，如：我的爆款套路1号"></el-input>
                        </el-form-item>
                        <el-form-item label="脚本内容" required>
                            <el-input v-model="extractForm.script_text" type="textarea" :rows="10"
                                placeholder="把你的爆款脚本/成功案例文案粘贴到这里，AI 会自动分析提炼其中的创作方法论..."></el-input>
                        </el-form-item>
                    </el-form>
                    <div style="color: #909399; font-size: 12px; margin-top: 4px;">支持口播稿、分镜脚本、视频文案等任意形式，字数不少于50字</div>
                </div>

                <div v-else>
                    <el-alert title="AI 提炼完成，请确认以下模板结构" type="success" :closable="false" style="margin-bottom: 16px;"></el-alert>
                    <el-descriptions :column="1" border>
                        <el-descriptions-item label="核心策略">{{ extractPreview.core_strategy }}</el-descriptions-item>
                        <el-descriptions-item label="开场公式">{{ extractPreview.hook_formula }}</el-descriptions-item>
                        <el-descriptions-item label="旁白风格">{{ extractPreview.narration_style }}</el-descriptions-item>
                        <el-descriptions-item label="第一幕">{{ extractPreview.structure && extractPreview.structure.act1 && extractPreview.structure.act1.name + '：' + extractPreview.structure.act1.description }}</el-descriptions-item>
                        <el-descriptions-item label="第二幕">{{ extractPreview.structure && extractPreview.structure.act2 && extractPreview.structure.act2.name + '：' + extractPreview.structure.act2.description }}</el-descriptions-item>
                        <el-descriptions-item label="第三幕">{{ extractPreview.structure && extractPreview.structure.act3 && extractPreview.structure.act3.name + '：' + extractPreview.structure.act3.description }}</el-descriptions-item>
                        <el-descriptions-item label="适合品类">{{ (extractPreview.suitable_categories || []).join('、') }}</el-descriptions-item>
                    </el-descriptions>
                </div>

                <template #footer>
                    <el-button @click="extractDialogVisible = false; extractPreview = null">取消</el-button>
                    <el-button v-if="extractPreview" @click="extractPreview = null">重新提炼</el-button>
                    <el-button v-if="!extractPreview" type="primary" @click="doExtract" :loading="extracting"
                        :disabled="!extractForm.name.trim() || extractForm.script_text.length < 50">
                        {{ extracting ? 'AI分析中...' : 'AI 提炼方法论' }}
                    </el-button>
                    <el-button v-if="extractPreview" type="success" @click="saveExtracted" :loading="saving">确认保存</el-button>
                </template>
            </el-dialog>

            <!-- ===== 克隆系统模板对话框 ===== -->
            <el-dialog v-model="cloneDialogVisible" title="📋 克隆系统模板" width="600px" :close-on-click-modal="false">
                <div v-if="!cloneTarget">
                    <p style="color: #606266; margin-bottom: 16px;">选择一个系统模板作为基础，克隆后可自由修改：</p>
                    <div v-for="tpl in systemTemplates" :key="tpl.template_id"
                        @click="cloneTarget = tpl"
                        :style="{ padding: '12px', marginBottom: '8px', border: '1px solid #e4e7ed', borderRadius: '8px', cursor: 'pointer', background: '#fafafa' }"
                        style="transition: all 0.15s;"
                        @mouseover="$event.currentTarget.style.borderColor='#409eff'"
                        @mouseleave="$event.currentTarget.style.borderColor='#e4e7ed'">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <strong>{{ tpl.name }}</strong>
                            <el-tag size="small" :type="sourceTagType(tpl.source.type)">{{ tpl.source.type === 'kol' ? 'KOL' : tpl.source.type === 'mcn' ? 'MCN' : '方法论' }}</el-tag>
                        </div>
                        <div style="font-size: 12px; color: #909399; margin-top: 4px;">{{ tpl.core_strategy }}</div>
                    </div>
                </div>

                <div v-else>
                    <el-alert :title="'基于「' + cloneTarget.name + '」创建'" type="info" :closable="false" style="margin-bottom: 16px;"></el-alert>
                    <el-form label-width="90px">
                        <el-form-item label="新模板名称" required>
                            <el-input v-model="cloneForm.new_name" :placeholder="'我的' + cloneTarget.name + '变体'"></el-input>
                        </el-form-item>
                        <el-form-item label="来源署名">
                            <el-input v-model="cloneForm.author_name" placeholder="如：我的账号名、品牌名（选填）"></el-input>
                        </el-form-item>
                        <el-form-item label="备注说明">
                            <el-input v-model="cloneForm.description" placeholder="这个模板的用途说明（选填）"></el-input>
                        </el-form-item>
                    </el-form>
                </div>

                <template #footer>
                    <el-button @click="cloneDialogVisible = false; cloneTarget = null">取消</el-button>
                    <el-button v-if="cloneTarget" @click="cloneTarget = null">重新选择</el-button>
                    <el-button v-if="cloneTarget" type="primary" @click="doClone" :loading="cloning"
                        :disabled="!cloneForm.new_name.trim()">克隆并保存</el-button>
                </template>
            </el-dialog>

            <!-- ===== 编辑模板对话框 ===== -->
            <el-dialog v-model="editDialogVisible" title="✏️ 编辑模板" width="680px" :close-on-click-modal="false">
                <el-form v-if="editTarget" label-width="90px">
                    <el-form-item label="模板名称">
                        <el-input v-model="editTarget.name"></el-input>
                    </el-form-item>
                    <el-form-item label="核心策略">
                        <el-input v-model="editTarget.core_strategy" type="textarea" :rows="3"></el-input>
                    </el-form-item>
                    <el-form-item label="开场公式">
                        <el-input v-model="editTarget.hook_formula" type="textarea" :rows="2"></el-input>
                    </el-form-item>
                    <el-form-item label="旁白风格">
                        <el-input v-model="editTarget.narration_style" placeholder="如：口语化+情感共鸣、理性干货型"></el-input>
                    </el-form-item>
                    <el-form-item label="第一幕描述">
                        <el-input v-model="editTarget.structure.act1.description" type="textarea" :rows="2"></el-input>
                    </el-form-item>
                    <el-form-item label="第二幕描述">
                        <el-input v-model="editTarget.structure.act2.description" type="textarea" :rows="2"></el-input>
                    </el-form-item>
                    <el-form-item label="第三幕描述">
                        <el-input v-model="editTarget.structure.act3.description" type="textarea" :rows="2"></el-input>
                    </el-form-item>
                    <el-form-item label="适合品类">
                        <el-input v-model="editTarget.suitable_categories_text" placeholder="多个品类用逗号分隔"></el-input>
                    </el-form-item>
                    <el-form-item label="推荐时长">
                        <el-input v-model="editTarget.best_duration" placeholder="如：60-90秒"></el-input>
                    </el-form-item>
                </el-form>
                <template #footer>
                    <el-button @click="editDialogVisible = false">取消</el-button>
                    <el-button type="primary" @click="saveEdit" :loading="saving">保存修改</el-button>
                </template>
            </el-dialog>
        </div>
    `,

    data() {
        return {
            activeTab: 'system',
            sourceFilter: null,
            sourceFilters: [
                { label: '全部', value: null },
                { label: 'KOL博主', value: 'kol' },
                { label: 'MCN机构', value: 'mcn' },
                { label: '营销方法论', value: 'methodology' }
            ],
            systemTemplates: [],
            userTemplates: [],
            loadingSystem: false,
            loadingUser: false,
            // 提炼
            extractDialogVisible: false,
            extractForm: { name: '', script_text: '' },
            extractPreview: null,
            extracting: false,
            saving: false,
            // 克隆
            cloneDialogVisible: false,
            cloneTarget: null,
            cloneForm: { new_name: '', author_name: '', description: '' },
            cloning: false,
            // 编辑
            editDialogVisible: false,
            editTarget: null,
        }
    },

    computed: {
        filteredSystemTemplates() {
            if (!this.sourceFilter) return this.systemTemplates;
            return this.systemTemplates.filter(t => t.source && t.source.type === this.sourceFilter);
        }
    },

    async mounted() {
        await Promise.all([this.loadSystem(), this.loadUser()]);
    },

    methods: {
        async loadSystem() {
            this.loadingSystem = true;
            try {
                const resp = await fetch('/api/templates/list');
                if (resp.ok) {
                    const data = await resp.json();
                    this.systemTemplates = data.templates || [];
                }
            } catch (e) {
                ElMessage.error('加载系统模板失败');
            } finally {
                this.loadingSystem = false;
            }
        },

        async loadUser() {
            this.loadingUser = true;
            try {
                const resp = await fetch('/api/user-templates/');
                if (resp.ok) {
                    const data = await resp.json();
                    this.userTemplates = data.templates || [];
                }
            } catch (e) {
                console.error('加载用户模板失败:', e);
            } finally {
                this.loadingUser = false;
            }
        },

        onTabChange(tab) {
            if (tab.paneName === 'user') this.loadUser();
        },

        sourceTagType(type) {
            return { kol: 'warning', mcn: 'danger', methodology: 'success' }[type] || 'info';
        },

        openCloneDialog(tpl) {
            this.cloneTarget = tpl;
            this.cloneForm = { new_name: '我的' + tpl.name, author_name: '', description: '' };
            this.cloneDialogVisible = true;
        },

        async doExtract() {
            if (!this.extractForm.name.trim() || this.extractForm.script_text.length < 50) return;
            this.extracting = true;
            try {
                const resp = await fetch('/api/user-templates/extract', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        script_text: this.extractForm.script_text,
                        template_name: this.extractForm.name
                    })
                });
                if (!resp.ok) throw new Error('提炼失败');
                const data = await resp.json();
                this.extractPreview = data.preview;
                this.extractPreview.name = this.extractForm.name;
                ElMessage.success('AI提炼完成，请确认模板结构');
            } catch (e) {
                ElMessage.error('AI提炼失败: ' + e.message);
            } finally {
                this.extracting = false;
            }
        },

        async saveExtracted() {
            this.saving = true;
            try {
                const resp = await fetch('/api/user-templates/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ...this.extractPreview, author_name: '自定义' })
                });
                if (!resp.ok) throw new Error('保存失败');
                ElMessage.success('模板保存成功！');
                this.extractDialogVisible = false;
                this.extractPreview = null;
                this.extractForm = { name: '', script_text: '' };
                this.activeTab = 'user';
                await this.loadUser();
            } catch (e) {
                ElMessage.error('保存失败: ' + e.message);
            } finally {
                this.saving = false;
            }
        },

        async doClone() {
            if (!this.cloneForm.new_name.trim()) return;
            this.cloning = true;
            try {
                const resp = await fetch('/api/user-templates/clone', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        template_id: this.cloneTarget.template_id,
                        new_name: this.cloneForm.new_name,
                        author_name: this.cloneForm.author_name || '自定义',
                        description: this.cloneForm.description
                    })
                });
                if (!resp.ok) throw new Error('克隆失败');
                ElMessage.success(`「${this.cloneForm.new_name}」已创建，可在「我的模板」中编辑`);
                this.cloneDialogVisible = false;
                this.cloneTarget = null;
                this.activeTab = 'user';
                await this.loadUser();
            } catch (e) {
                ElMessage.error('克隆失败: ' + e.message);
            } finally {
                this.cloning = false;
            }
        },

        openEditDialog(tpl) {
            // 深拷贝防止直接修改原对象
            this.editTarget = JSON.parse(JSON.stringify(tpl));
            this.editTarget.suitable_categories_text = (tpl.suitable_categories || []).join('、');
            this.editDialogVisible = true;
        },

        async saveEdit() {
            this.saving = true;
            try {
                const updates = {
                    name: this.editTarget.name,
                    core_strategy: this.editTarget.core_strategy,
                    hook_formula: this.editTarget.hook_formula,
                    narration_style: this.editTarget.narration_style,
                    structure: this.editTarget.structure,
                    suitable_categories: this.editTarget.suitable_categories_text
                        ? this.editTarget.suitable_categories_text.split(/[,，、]/).map(s => s.trim()).filter(Boolean)
                        : [],
                    best_duration: this.editTarget.best_duration
                };
                const resp = await fetch(`/api/user-templates/${this.editTarget.template_id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(updates)
                });
                if (!resp.ok) throw new Error('保存失败');
                ElMessage.success('修改已保存');
                this.editDialogVisible = false;
                await this.loadUser();
            } catch (e) {
                ElMessage.error('保存失败: ' + e.message);
            } finally {
                this.saving = false;
            }
        },

        async deleteUserTemplate(tpl) {
            try {
                await ElMessageBox.confirm(`确定删除「${tpl.name}」吗？`, '确认删除', {
                    confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning'
                });
            } catch { return; }
            try {
                const resp = await fetch(`/api/user-templates/${tpl.template_id}`, { method: 'DELETE' });
                if (!resp.ok) throw new Error('删除失败');
                ElMessage.success('模板已删除');
                await this.loadUser();
            } catch (e) {
                ElMessage.error('删除失败: ' + e.message);
            }
        }
    }
});

// 使用Element Plus
app.use(ElementPlus);

// 注册Element Plus图标组件（CDN模式必须手动注册）
if (window.ElementPlusIconsVue) {
    for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
        app.component(key, component);
    }
    console.log('Element Plus Icons已注册');
}

// 挂载应用
app.mount('#app');

console.log('Vue应用已加载');
