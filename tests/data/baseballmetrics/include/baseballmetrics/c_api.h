#ifndef BASEBALLMETRICS_C_API_H_
#define BASEBALLMETRICS_C_API_H_

/** exporting symbols **/

#ifdef __cplusplus
#define BASEBALLMETRICS_EXTERN_C extern "C"
#else
#define BASEBALLMETRICS_EXTERN_C
#endif

BASEBALLMETRICS_EXTERN_C double BattingAverage(
    const int hits,
    const int at_bats
);

#endif /** BASEBALLMETRICS_EXPORT_H_ **/
