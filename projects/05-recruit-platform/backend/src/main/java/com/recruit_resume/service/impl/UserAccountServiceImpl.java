package com.recruit_resume.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.recruit_resume.entity.UserAccount;
import com.recruit_resume.mapper.UserAccountMapper;
import com.recruit_resume.service.UserAccountService;
import org.springframework.stereotype.Service;

@Service
public class UserAccountServiceImpl extends ServiceImpl<UserAccountMapper, UserAccount> implements UserAccountService {
}
