<script setup lang="ts">
import { ref } from 'vue'

const itPlat = ref('微信公众号')
const itTitle = ref('')
const itStyle = ref('专业严谨')
const itContent = ref('')
</script>

<template>
  <div class="it-wrap">
    <!-- Left: input -->
    <div class="it-left">
      <div class="it-left-hd">
        <div class="it-left-t">
          AI 智能排版与预览中心
          <span class="it-left-tag">BETA</span>
        </div>
        <div class="it-left-d">快速生成多平台适配的精美排版，实时预览效果</div>
      </div>

      <div class="it-sec">
        <div class="it-sec-t">✏️ 内容输入</div>

        <div class="it-fg">
          <div class="it-fg-l">目标平台</div>
          <div class="it-plats">
            <button v-for="p in ['微信公众号', '小红书', '抖音']" :key="p"
              class="it-plat" :class="{ on: itPlat === p }" @click="itPlat = p">{{ p }}</button>
          </div>
        </div>

        <div class="it-fg">
          <div class="it-fg-l">
            标题
            <span class="it-fg-ct">{{ itTitle.length }}/30</span>
          </div>
          <input class="it-inp" v-model="itTitle" @input="itTitle = itTitle.slice(0, 30)" placeholder="请输入吸引人的标题..." />
        </div>

        <div class="it-fg">
          <div class="it-fg-l">语气风格</div>
          <select class="it-sel" v-model="itStyle">
            <option>专业严谨</option><option>轻松活泼</option><option>温暖治愈</option><option>幽默搞笑</option><option>简洁干练</option>
          </select>
        </div>

        <div class="it-fg">
          <div class="it-fg-l">
            正文内容
            <span class="it-fg-link">导入文档</span>
          </div>
          <textarea class="it-inp" rows="10" v-model="itContent" @input="itContent = itContent.slice(0, 2000)"
            placeholder="在此输入或粘贴您的文章内容..." style="resize:vertical;" />
          <div style="text-align:right;font-size:10px;color:var(--t3);margin-top:4px;">{{ itContent.length }}/2000 字</div>
        </div>

        <button class="it-gen-btn">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l2.4 7.2L22 12l-7.6 2.8L12 22l-2.4-7.2L2 12l7.6-2.8z"/></svg>
          AI 智能排版
        </button>

        <div class="it-tip" style="display:flex;gap:8px;padding:12px 14px;background:var(--s2);border-radius:10px;border:1px solid var(--bl);">
          <div style="width:28px;height:28px;border-radius:7px;background:var(--pbg);color:var(--p);display:flex;align-items:center;justify-content:center;flex-shrink:0;">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18h6"/><path d="M10 22h4"/><path d="M12 2a7 7 0 0 0-4 12.7V17h8v-2.3A7 7 0 0 0 12 2z"/></svg>
          </div>
          <div>
            <div style="font-size:11px;font-weight:600;color:var(--t2);margin-bottom:2px;">排版小贴士</div>
            <div style="font-size:10px;color:var(--t3);line-height:1.5;">尝试在正文中添加 "##" 作为小标题，AI 能更准确地识别文章结构并生成更有层次感的排版。</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Right: preview -->
    <div class="it-right">
      <div class="it-preview">
        <div class="it-pv-empty">
          <div class="it-pv-ic">✨</div>
          <div class="it-pv-t">等待生成预览</div>
          <div class="it-pv-d">在左侧面板输入内容并点击<br>"AI 智能排版" 即可查看效果</div>
          <div class="it-pv-skel">
            <div class="it-pv-skel-line w60" />
            <div class="it-pv-skel-line w80" />
            <div class="it-pv-skel-block" />
            <div class="it-pv-skel-line w80" />
            <div class="it-pv-skel-line w40" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
