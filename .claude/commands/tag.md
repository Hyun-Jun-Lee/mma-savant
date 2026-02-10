# Smart Git Tag Command

이전 태그 이후의 커밋들을 분석하여 annotated tag 메시지를 작성합니다.

## 작업 순서

1. **현재 태그 상태 확인**
   - `git tag --list 'v*' --sort=-version:refname` 로 최신 태그 확인
   - 태그가 없으면 최초 커밋부터 분석

2. **커밋 히스토리 분석**
   - `git log [prev-tag]..HEAD --oneline` 으로 변경사항 수집
   - Conventional Commits 형식 기준으로 분류:
     - `feat`: 새로운 기능
     - `fix`: 버그 수정
     - `docs`: 문서 변경
     - `style`: 코드 스타일 변경
     - `refactor`: 리팩토링
     - `test`: 테스트 추가/수정
     - `chore`: 빌드, 설정 등 기타 변경

3. **다음 버전 제안**
   - Major (v1.0.0 → v2.0.0): Breaking changes
   - Minor (v0.1.0 → v0.2.0): 새 기능 추가
   - Patch (v0.1.0 → v0.1.1): 버그 수정, 작은 개선

4. **태그 메시지 생성**
   ```
   v0.2.0 - [릴리스 제목]

   ## Features
   - 새로운 기능 설명

   ## Bug Fixes
   - 수정된 버그 설명

   ## Changes
   - 기타 변경사항
   ```

5. **출력 형식**
   ```
   ### 릴리스 분석

   **이전 태그**: v0.1.0
   **제안 버전**: v0.2.0 (Minor - 새 기능 추가)

   **커밋 분류**:
   - feat: 3개
   - fix: 2개
   - chore: 1개

   ---

   ### Git 명령어

   ```bash
   git tag -a v0.2.0 \
     -m "v0.2.0 - 사용자 인증 기능 추가" \
     -m "## Features" \
     -m "- JWT 기반 사용자 인증 구현" \
     -m "- 소셜 로그인 (Google, GitHub) 지원" \
     -m "## Bug Fixes" \
     -m "- 로그인 타임아웃 문제 해결" \
     -m "## Changes" \
     -m "- 의존성 업데이트"
   ```

   **태그 푸시**:
   ```bash
   git push origin v0.2.0
   ```
   ```

## 주의사항

- 실제 태그 생성은 실행하지 않고 제안만 제공
- 커밋 메시지가 Conventional Commits 형식이 아니면 수동 분류 필요
- Breaking changes가 있으면 반드시 Major 버전 증가 권장
- 태그 푸시 전 로컬에서 검증 권장
