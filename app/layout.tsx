import type { Metadata } from 'next';
import './globals.css';
import './tablet-ui.css';

export const metadata: Metadata = {
  title: '나주 산책',
  description: '나주의 골목과 강변, 빛가람 호수공원과 수목원을 3D로 산책합니다. 실제 지도와 사진을 참고한 체험 모형입니다.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body>
        {children}
      </body>
    </html>
  );
}
