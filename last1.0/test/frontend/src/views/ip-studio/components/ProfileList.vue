<script setup lang="ts">
import { useIPStudioStore } from '../../../stores/ipStudio'
import { ElMessageBox } from 'element-plus'

const store = useIPStudioStore()

const startNew = () => {
  store.resetInterview()
  store.goToView('interview')
}

const openWorkspace = async (profileId: string) => {
  await store.loadProfile(profileId)
  await store.loadTopics(profileId)
  store.goToView('detail')
}

const deleteProfile = async (profileId: string) => {
  try {
    await ElMessageBox.confirm('确定删除此IP档案？此操作不可撤销。', '删除确认', { type: 'warning' })
    await store.removeProfile(profileId)
  } catch { /* cancelled */ }
}

const formatDate = (d: string) => d ? d.slice(0, 10) : ''
</script>

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
      <div style="color: #606266; font-size: 14px;">为你的个人IP打造专属选题库和脚本，听起来像你自己写的</div>
      <el-button type="warning" size="large" @click="startNew">🎙️ 新建IP档案（AI访谈）</el-button>
    </div>

    <el-empty v-if="store.profiles.length === 0 && !store.loading" description="还没有IP档案，点击右上角新建" />

    <el-row :gutter="20" v-loading="store.loading">
      <el-col :span="8" v-for="p in store.profiles" :key="p.profile_id" style="margin-bottom: 20px;">
        <el-card shadow="hover" style="cursor: pointer;" @click="openWorkspace(p.profile_id)">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <div>
                <span style="font-size: 18px; font-weight: bold;">{{ p.name }}</span>
                <el-tag size="small" type="warning" style="margin-left: 8px;">{{ p.industry }}</el-tag>
                <span v-if="p.role" style="font-size: 12px; color: #909399; margin-left: 6px;">{{ p.role }}</span>
              </div>
              <el-button text type="danger" size="small" @click.stop="deleteProfile(p.profile_id)">删除</el-button>
            </div>
          </template>
          <p style="font-size: 13px; color: #606266; margin: 0 0 12px; line-height: 1.6;">{{ p.ip_positioning }}</p>
          <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px;">
            <el-tag v-for="pillar in (p.content_pillars || []).slice(0, 3)" :key="pillar" size="small" type="info">{{ pillar }}</el-tag>
          </div>
          <div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: #909399;">
            <span>已有 {{ p.topic_count || 0 }} 个选题</span>
            <span>{{ formatDate(p.created_at) }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
