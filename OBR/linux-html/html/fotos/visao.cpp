#include <opencv2/opencv.hpp>
#include <chrono>
#include <iostream>

using namespace cv;
using namespace std;

int main()
{
    auto t0 = chrono::high_resolution_clock::now();

    Mat img = imread("foto.jpg");

    if(img.empty())
    {
        cout << "Erro ao abrir foto.jpg\n";
        return 1;
    }

    auto t1 = chrono::high_resolution_clock::now();

    resize(img, img, Size(80,60));

    auto t2 = chrono::high_resolution_clock::now();

    for(int y=0; y<img.rows; y++)
    {
        for(int x=0; x<img.cols; x++)
        {
            Vec3b p = img.at<Vec3b>(y,x);

            int B = p[0];
            int G = p[1];
            int R = p[2];

            char c='X';

            if(
                G > 80 &&
                G > R + 25 &&
                G > B + 25
            )
            {
                c='G';
            }
            else if(
                R > 170 &&
                G > 170 &&
                B > 170
            )
            {
                c='W';
            }
            else if(
                R < 50 &&
                G < 50 &&
                B < 50
            )
            {
                c='P';
            }

            cout << c;
        }

        cout << '\n';
    }

    auto t3 = chrono::high_resolution_clock::now();

    double leitura =
        chrono::duration<double,milli>(t1-t0).count();

    double resizeTempo =
        chrono::duration<double,milli>(t2-t1).count();

    double procTempo =
        chrono::duration<double,milli>(t3-t2).count();

    cout << "\n";
    cout << "Leitura : " << leitura << " ms\n";
    cout << "Resize  : " << resizeTempo << " ms\n";
    cout << "Process : " << procTempo << " ms\n";

    return 0;
}