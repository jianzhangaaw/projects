<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'

import { useAuthStore } from '@/stores/auth'
import { listExperiencesByStudent, createExperience, updateExperience, deleteExperience } from '@/api/student'
import ModuleCard from '@/components/ModuleCard.vue'
import type { StudentExperience } from '@/types/api'

const auth = useAuthStore()
const experiences = ref<StudentExperience[]>([])
const showAddDialog = ref(false)
const editingExperience = ref<StudentExperience | null>(null)
const detailMode = ref(false)
const formRef = ref<FormInstance>()
const fileList = ref<any[]>([])

const uploadUrl = '/api/files/upload'

const getUploadHeaders = () => {
  const raw = localStorage.getItem('auth')
  let token = ''
  try {
    token = raw ? JSON.parse(raw).token : ''
  } catch {
    localStorage.removeItem('auth')
  }
  return { Authorization: `Bearer ${token}` }
}

const form = reactive({
  experienceType: 'PROJECT',
  title: '',
  timeRange: '',
  roleName: '',
  description: '',
  fileId: null as number | null
})

const rules = {
  experienceType: [{ required: true, message: '请选择经历类型', trigger: 'change' }],
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  timeRange: [{ required: true, message: '请输入时间范围', trigger: 'blur' }]
}

const experienceTypeOptions = [
  { label: '项目经验', value: 'PROJECT' },
  { label: '实习经历', value: 'INTERNSHIP' },
  { label: '竞赛荣誉', value: 'COMPETITION_HONOR' }
]

const getType = (type: string) => {
  const types: Record<string, string> = { PROJECT: 'info', INTERNSHIP: 'warning', COMPETITION_HONOR: 'success' }
  return types[type] || 'info'
}

const getTypeText = (type: string) => {
  const texts: Record<string, string> = { PROJECT: '项目经验', INTERNSHIP: '实习经历', COMPETITION_HONOR: '竞赛荣誉' }
  return texts[type] || type
}

const loadExperiences = async () => {
  try {
    const result = await listExperiencesByStudent(auth.userId!)
    if (result) {
      experiences.value = result
    }
  } catch (error) {
    ElMessage.error('加载经历失败')
  }
}

const uploadSuccess = (response: any) => {
  if (response.code === 200 && response.data) {
    form.fileId = response.data.fileId || response.data.id
  }
}

const removeFile = () => {
  form.fileId = null
}

const buildPayload = (): StudentExperience => ({
  experienceType: form.experienceType,
  title: form.title,
  timeRange: form.timeRange,
  roleName: form.roleName,
  description: form.description,
  fileId: form.fileId ?? undefined,
})

const editExperienceItem = (experience: StudentExperience) => {
  detailMode.value = false
  editingExperience.value = experience
  form.experienceType = experience.experienceType || 'PROJECT'
  form.title = experience.title || ''
  form.timeRange = experience.timeRange || ''
  form.roleName = experience.roleName || ''
  form.description = experience.description || ''
  form.fileId = experience.fileId || null
  fileList.value = experience.fileUrl ? [{ name: '已上传文件', url: experience.fileUrl }] : []
  showAddDialog.value = true
}

function onRowClick(row: StudentExperience) {
  detailMode.value = true
  editExperienceItem(row)
}

const deleteExperienceItem = async (experience: StudentExperience) => {
  try {
    await ElMessageBox.confirm('确定要删除该经历吗？', '提示', { type: 'warning' })
  } catch {
    return
  }
  try {
    await deleteExperience(experience.id!)
    ElMessage.success('删除成功')
    loadExperiences()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

const saveExperience = async () => {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  try {
    if (editingExperience.value) {
      await updateExperience(editingExperience.value.id!, buildPayload())
      ElMessage.success('更新成功')
    } else {
      await createExperience(buildPayload())
      ElMessage.success('添加成功')
    }
    showAddDialog.value = false
    editingExperience.value = null
    detailMode.value = false
    form.experienceType = 'PROJECT'
    form.title = ''
    form.timeRange = ''
    form.roleName = ''
    form.description = ''
    form.fileId = null
    fileList.value = []
    loadExperiences()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

onMounted(loadExperiences)
</script>

<template>
  <div class="student-experience">
    <ModuleCard title="经历管理" subtitle="管理项目经验、实习经历和竞赛荣誉">
      <template #actions>
        <el-button type="primary" @click="showAddDialog = true">添加经历</el-button>
      </template>

      <el-table :data="experiences" stripe @row-click="onRowClick">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="experienceType" label="类型" width="120">
          <template #default="scope">
            <el-tag :type="getType(scope.row.experienceType)">
              {{ getTypeText(scope.row.experienceType) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" show-overflow-tooltip />
        <el-table-column prop="timeRange" label="时间范围" width="150" show-overflow-tooltip />
        <el-table-column prop="roleName" label="角色/职务" show-overflow-tooltip />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column label="佐证材料" width="150">
          <template #default="scope">
            <el-link v-if="scope.row.fileUrl" type="primary" :href="scope.row.fileUrl" target="_blank">
              查看
            </el-link>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="添加时间" width="170" />
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button size="small" @click.stop="editExperienceItem(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click.stop="deleteExperienceItem(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </ModuleCard>

    <el-dialog v-model="showAddDialog" :title="detailMode ? '经历详情' : editingExperience ? '编辑经历' : '添加经历'" width="600px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" :disabled="detailMode">
        <el-form-item label="经历类型" prop="experienceType">
          <el-select v-model="form.experienceType">
            <el-option v-for="item in experienceTypeOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" />
        </el-form-item>
        <el-form-item label="时间范围" prop="timeRange">
          <el-input v-model="form.timeRange" placeholder="如：2024-01 至 2024-06" />
        </el-form-item>
        <el-form-item label="角色/职务" prop="roleName">
          <el-input v-model="form.roleName" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="4" />
        </el-form-item>
        <el-form-item label="佐证材料" v-if="!detailMode">
          <el-upload
            class="upload-demo"
            :action="uploadUrl"
            :headers="getUploadHeaders()"
            :data="{ businessType: 'CERTIFICATE' }"
            :on-success="uploadSuccess"
            :on-remove="removeFile"
            :file-list="fileList"
            :limit="1"
            :accept="'.pdf,.doc,.docx,.jpg,.jpeg,.png'"
          >
            <el-button size="small" type="primary">点击上传</el-button>
            <template #tip>
              <div class="el-upload__tip">支持上传项目报告、实习证明、获奖证书等佐证材料，格式为pdf、doc、docx、jpg、png，最多1个文件</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button v-if="detailMode" @click="showAddDialog = false">关闭</el-button>
        <template v-else>
          <el-button @click="showAddDialog = false">取消</el-button>
          <el-button type="primary" @click="saveExperience">确定</el-button>
        </template>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.upload-demo {
  margin-top: 5px;
}

:deep(.el-table__body tr) {
  cursor: pointer;
}
</style>
