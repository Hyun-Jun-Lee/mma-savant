# Smart Git Commit Command

현재 git status를 확인한 후, 변경사항을 논리적으로 그룹화하여 적절한 commit message를 작성합니다.

## 작업 순서

1. **git status 확인**
   - 현재 staged, unstaged, untracked 파일들을 모두 확인

2. **변경사항 분석**
   - 각 파일의 변경 내용을 git diff로 확인
   - 논리적으로 연관된 변경사항끼리 그룹화

3. **그룹별 커밋 제안**
   - 각 그룹에 대해:
     - 어떤 파일들을 git add 해야 하는지
     - 해당 그룹의 commit message (conventional commits 형식)
   - 여러 그룹이 있으면 순서대로 나열

4. **Commit Message 형식**
   - Conventional Commits 형식 사용 (feat, fix, docs, style, refactor, test, chore)
   - 간결하고 명확한 제목 (50자 이내)
   - 필요시 본문 추가 (What & Why)
   - Claude 작성 관련 footer는 제외

5. **출력 형식**
   ```
   ### 그룹 1: [그룹 설명]

   **파일 목록:**
   - file1.py
   - file2.py

   **Git 명령어:**
   ```bash
   git add file1.py file2.py
   git commit -m "feat: add user authentication feature

   - Implement JWT token generation
   - Add login/logout endpoints
   - Update user model with password hashing"
   ```

   ---

   ### 그룹 2: [그룹 설명]
   ...
   ```

## 주의사항

- 서로 관련 없는 변경사항은 별도 커밋으로 분리
- 테스트 파일 변경은 해당 기능과 함께 커밋
- 문서 변경은 별도 커밋으로 분리 가능
- 실제 git commit은 실행하지 않고 제안만 제공