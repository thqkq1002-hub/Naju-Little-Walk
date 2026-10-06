import type { Metadata } from 'next';
import './globals.css';
import './tablet-ui.css';

export const metadata: Metadata = {
  title: '나주 산책',
  description: '나주 전체 지도에서 금성관, 영산포, 빛가람동, 수목원과 드들강을 선택해 3D로 산책합니다. 공식 사진과 지도 자료를 참고한 지역 탐험 모형입니다.',
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
