#include <baseballmetrics/c_api.h>

double BattingAverage(
    const int hits,
    const int at_bats
) {
    return static_cast<float>(hits) / static_cast<float>(at_bats);
}
