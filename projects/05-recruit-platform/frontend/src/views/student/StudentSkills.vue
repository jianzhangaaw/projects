<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'

import { useAuthStore } from '@/stores/auth'
import { listSkillsByStudent, createSkill, updateSkill, deleteSkill } from '@/api/student'
import ModuleCard from '@/components/ModuleCard.vue'
import type { StudentSkill } from '@/types/api'

const auth = useAuthStore()
const skills = ref<StudentSkill[]>([])
const showAddDialog = ref(false)
const editingSkill = ref<StudentSkill | null>(null)
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
  skillName: '',
  skillType: '',
  proficiency: '',
  years: 0,
  fileId: null as number | null
})

const rules = {
  skillName: [{ required: true, message: '请输入技能名称', trigger: 'blur' }]
}

const proficiencyOptions = [
  { label: '了解', value: '了解' },
  { label: '熟悉', value: '熟悉' },
  { label: '掌握', value: '掌握' },
  { label: '精通', value: '精通' }
]

const getProficiencyType = (proficiency: string) => {
  const types: Record<string, string> = { '了解': 'info', '熟悉': 'warning', '掌握': 'success', '精通': 'danger' }
  return types[proficiency] || 'info'
}

const loadSkills = async () => {
  try {
    const result = await listSkillsByStudent(auth.userId!)
    if (result) {
      skills.value = result
    }
  } catch (error) {
    ElMessage.error('加载技能失败')
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

const buildPayload = (): StudentSkill => ({
  skillName: form.skillName,
  skillType: form.skillType,
  proficiency: form.proficiency,
  years: form.years,
  fileId: form.fileId ?? undefined,
})

const editSkill = (skill: StudentSkill) => {
  detailMode.value = false
  editingSkill.value = skill
  form.skillName = skill.skillName || ''
  form.skillType = skill.skillType || ''
  form.proficiency = skill.proficiency || ''
  form.years = skill.years || 0
  form.fileId = skill.fileId || null
  fileList.value = skill.fileUrl ? [{ name: '已上传文件', url: skill.fileUrl }] : []
  showAddDialog.value = true
}

function onRowClick(row: StudentSkill) {
  detailMode.value = true
  editSkill(row)
}

const deleteSkillItem = async (skill: StudentSkill) => {
  try {
    await ElMessageBox.confirm('确定要删除该技能吗？', '提示', { type: 'warning' })
  } catch {
    return
  }
  try {
    await deleteSkill(skill.id!)
    ElMessage.success('删除成功')
    loadSkills()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

const saveSkill = async () => {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
  } catch {
    return
  }
  try {
    if (editingSkill.value) {
      await updateSkill(editingSkill.value.id!, buildPayload())
      ElMessage.success('更新成功')
    } else {
      await createSkill(buildPayload())
      ElMessage.success('添加成功')
    }
    showAddDialog.value = false
    editingSkill.value = null
    detailMode.value = false
    form.skillName = ''
    form.skillType = ''
    form.proficiency = ''
    form.years = 0
    form.fileId = null
    fileList.value = []
    loadSkills()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

onMounted(loadSkills)
</script>

<template>
  <div class="student-skill">
    <ModuleCard title="技能管理" subtitle="管理个人技能和佐证材料">
      <template #actions>
        <el-button type="primary" @click="showAddDialog = true">添加技能</el-button>
      </template>

      <el-table :data="skills" stripe @row-click="onRowClick">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="skillName" label="技能名称" show-overflow-tooltip />
        <el-table-column prop="skillType" label="技能分类" show-overflow-tooltip />
        <el-table-column prop="proficiency" label="熟练度" width="100">
          <template #default="scope">
            <el-tag :type="getProficiencyType(scope.row.proficiency)">
              {{ scope.row.proficiency || '-' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="years" label="使用年限" width="100" />
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
            <el-button size="small" @click.stop="editSkill(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click.stop="deleteSkillItem(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </ModuleCard>

    <el-dialog v-model="showAddDialog" :title="detailMode ? '技能详情' : editingSkill ? '编辑技能' : '添加技能'" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" :disabled="detailMode">
        <el-form-item label="技能名称" prop="skillName">
          <el-input v-model="form.skillName" />
        </el-form-item>
        <el-form-item label="技能分类" prop="skillType">
          <el-input v-model="form.skillType" />
        </el-form-item>
        <el-form-item label="熟练度" prop="proficiency">
          <el-select v-model="form.proficiency">
            <el-option v-for="item in proficiencyOptions" :key="item.value" :label="item.label" :value="item.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="使用年限" prop="years">
          <el-input-number v-model="form.years" :min="0" :max="50" :step="0.5" />
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
              <div class="el-upload__tip">支持上传证书、成绩单等佐证材料，格式为pdf、doc、docx、jpg、png，最多1个文件</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button v-if="detailMode" @click="showAddDialog = false">关闭</el-button>
        <template v-else>
          <el-button @click="showAddDialog = false">取消</el-button>
          <el-button type="primary" @click="saveSkill">确定</el-button>
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
