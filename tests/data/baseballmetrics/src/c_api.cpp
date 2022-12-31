#include <baseballmetrics/c_api.h>

void BattingAverage(
    const int hits,
    const int at_bats,
    double* ret
) {
    *ret = static_cast<double>(hits) / static_cast<double>(at_bats);
}
