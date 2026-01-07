import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Docker 배포를 위한 standalone 출력 모드
  output: "standalone",
};

export default nextConfig;
