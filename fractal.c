void mandelbrot(
    int max, int width, int height,
    double wx, double wy, double ww, double wh,
    unsigned int *palette, int palette_size,
    unsigned int *data)
{
    int index = 0;
    double dx = ww / width;
    double dy = wh / height;
    double y0 = wy + wh;
    for (int _y = 0; _y < height; _y++) {
        double x0 = wx;
        for (int _x = 0; _x < width; _x++) {
            double x = 0;
            double y = 0;
            int iteration = 0;
            while (x * x + y * y < 4 && iteration < max) {
                double temp = x * x - y * y + x0;
                y = 2 * x * y + y0;
                x = temp;
                iteration++;
            }
            data[index++] = iteration == max ? 0xff000000 :
                palette[(iteration - 1) % palette_size];
            x0 += dx;
        }
        y0 -= dy;
    }
}

void julia(
    int max, int width, int height,
    double wx, double wy, double ww, double wh,
    double jx, double jy,
    unsigned int *palette, int palette_size,
    unsigned int *data)
{
    int index = 0;
    double dx = ww / width;
    double dy = wh / height;
    double y0 = wy + wh;
    for (int _y = 0; _y < height; _y++) {
        double x0 = wx;
        for (int _x = 0; _x < width; _x++) {
            double x = x0;
            double y = y0;
            int iteration = 1;
            while (x * x + y * y < 4 && iteration < max) {
                double temp = x * x - y * y + jx;
                y = 2 * x * y + jy;
                x = temp;
                iteration++;
            }
            data[index++] = iteration == max ? 0xff000000 :
                palette[(iteration - 1) % palette_size];
            x0 += dx;
        }
        y0 -= dy;
    }
}
